import logging
import traceback
from typing import Annotated

import starlette.status as status
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastui import AnyComponent, FastUI, prebuilt_html
from fastui import components as c
from fastui.forms import SelectSearchResponse, fastui_form
from samba.samdb import SamDB

from guam import config, smb
from guam.components import layout
from guam.models.autofs import AutoFSGroup, AutoFSMount
from guam.models.secgroup import SecurityGroup
from guam.models.user import User
from guam.utils import autofs, groups, users

router = APIRouter()
logger = logging.getLogger("uvicorn.error")

# Needed to prevent this problem: https://errors.pydantic.dev/2.10/u/class-not-fully-defined
c.ModelForm.model_rebuild()


def get_smb():
    samdb = smb.connect()
    try:
        yield samdb
    finally:
        # TODO: The version of samdb currently running in production does not have disconnect()
        # samdb.disconnect()
        samdb = None


@router.get("/api/forms/servers", response_model=SelectSearchResponse)
async def search_view(
    request: Request,
    q: str,
) -> SelectSearchResponse:
    servers: list[str] = config.afsserverlist
    servers = [server for server in servers if server.startswith(q)]
    options = []

    for server in servers:
        options.append({"value": server, "label": server})

    return SelectSearchResponse(options=options)


@router.get("/api/forms/departments", response_model=SelectSearchResponse)
async def search_view(
    request: Request,
    q: str,
) -> SelectSearchResponse:
    departments: list[str] = config.departmentlist
    departments = [department for department in departments if department.startswith(q)]
    options = []

    for department in departments:
        options.append({"value": department, "label": department})

    return SelectSearchResponse(options=options)


@router.get("/api/forms/afsgroups", response_model=SelectSearchResponse)
async def search_view(
    request: Request,
    q: str,
    samdb: Annotated[SamDB, Depends(get_smb)],
) -> SelectSearchResponse:
    afsgroups = autofs.afsgroups(samdb, q)

    options = []
    for afsgroup in afsgroups:
        options.append({"value": afsgroup, "label": afsgroup})

    return SelectSearchResponse(options=options)


@router.get("/api/forms/secgroups", response_model=SelectSearchResponse)
async def search_view(
    request: Request,
    q: str,
    samdb: Annotated[SamDB, Depends(get_smb)],
) -> SelectSearchResponse:
    secgroups = list(groups.secgroups(samdb, q).keys())
    secgroups.sort(key=str.casefold)

    options = []
    for secgroup in secgroups:
        options.append({"value": secgroup, "label": secgroup})

    return SelectSearchResponse(options=options)


@router.get("/api/users", response_model=FastUI, response_model_exclude_none=True)
def user_get():
    # c.ModelForm.model_rebuild()
    form = c.ModelForm(model=User, submit_url="/api/users")
    return layout([form], title="Add New User")


@router.post("/api/users", response_model=FastUI, response_model_exclude_none=True)
def user_post(
    form: Annotated[User, fastui_form(User)],
    samdb: Annotated[SamDB, Depends(get_smb)],
) -> list[AnyComponent]:
    try:
        user = users.add_user(samdb, form)
    except Exception as e:
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))
    return layout(
        [c.Heading(text="User Added"), c.Details(data=user)], title="User Added"
    )


@router.get("/api/afsmounts", response_model=FastUI, response_model_exclude_none=True)
async def afsmounts_get():
    return layout(
        [c.ModelForm(model=AutoFSMount, submit_url="/api/afsmounts")],
        title="Add New Mount to AutoFS",
    )


@router.post("/api/afsmounts", response_model=FastUI, response_model_exclude_none=True)
def afsmounts_post(
    form: Annotated[AutoFSMount, fastui_form(AutoFSMount)],
    samdb: Annotated[SamDB, Depends(get_smb)],
) -> list[AnyComponent]:
    try:
        mount = autofs.addAutofsEntry(samdb, form)
        print(mount)
    except Exception as e:
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))

    return layout(
        [c.Heading(text="AutoFS Mount Added"), c.Details(data=mount)],
        title="AutoFS Mount Added",
    )


@router.get("/api/afsgroups", response_model=FastUI, response_model_exclude_none=True)
async def afsgroups_get():
    return layout(
        [c.ModelForm(model=AutoFSGroup, submit_url="/api/afsgroups")],
        title="Add New AutoFS Group",
    )


@router.post("/api/afsgroups", response_model=FastUI, response_model_exclude_none=True)
def afsgroups_post(
    form: Annotated[AutoFSGroup, fastui_form(AutoFSGroup)],
    samdb: Annotated[SamDB, Depends(get_smb)],
) -> list[AnyComponent]:
    try:
        groups = autofs.addAutofsGroup(samdb, form)
        markdown = ""
        for group in groups:
            markdown += f"- {group}\n"

    except Exception as e:
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))

    return layout(
        [c.Heading(text="AutoFS Groups Added"), c.Markdown(text=markdown)],
        title="AutoFS Groups Added",
    )


@router.get("/api/secgroups", response_model=FastUI, response_model_exclude_none=True)
async def secgroups_get():
    return layout(
        [c.ModelForm(model=SecurityGroup, submit_url="/api/secgroups")],
        title="Create New Security Group",
    )


@router.post("/api/secgroups", response_model=FastUI, response_model_exclude_none=True)
def secgroups_post(
    form: Annotated[SecurityGroup, fastui_form(SecurityGroup)],
    samdb: Annotated[SamDB, Depends(get_smb)],
) -> list[AnyComponent]:
    try:
        group = groups.add_sec_group(samdb, form)
    except Exception as e:
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))
    return layout(
        [c.Heading(text="Security Group Added"), c.Details(data=group)],
        title="Security Group Added",
    )


@router.get("/")
async def index():
    # Redirect to /docs (relative URL)
    return RedirectResponse(url="/users", status_code=status.HTTP_302_FOUND)


# IMPORTANT: This route should be the last route in this file!!!!!!!
@router.get("/{path:path}")
def root() -> HTMLResponse:
    """Simple HTML page which serves the React app, comes last as it matches all paths."""
    return HTMLResponse(prebuilt_html(title="Guam"))
