from typing import Annotated

import starlette.status as status
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastui import AnyComponent, FastUI, prebuilt_html
from fastui import components as c
from fastui.events import GoToEvent
from fastui.forms import SelectSearchResponse, fastui_form
from ldb import LdbError
from samba.samdb import SamDB

from app import config, smb
from app.models.autofs import AutoFSGroup, AutoFSMount
from app.models.secgroup import SecurityGroup
from app.models.user import User
from app.utils import autofs, groups, users

router = APIRouter()


def get_smb():
    samdb = smb.connect()
    try:
        yield samdb
    finally:
        samdb.disconnect()


def layout(*components: AnyComponent, title: str) -> list[AnyComponent]:
    return [
        c.PageTitle(text=title),
        c.Navbar(
            title="GUAM",
            title_event=GoToEvent(url="/users"),
            start_links=[
                c.Link(
                    components=[c.Text(text="User")],
                    on_click=GoToEvent(url="/users"),
                    active="startswith:/users",
                ),
                c.Link(
                    components=[c.Text(text="AFS Mount")],
                    on_click=GoToEvent(url="/afsmounts"),
                    active="startswith:/afsmounts",
                ),
                c.Link(
                    components=[c.Text(text="AFS Group")],
                    on_click=GoToEvent(url="/afsgroups"),
                    active="startswith:/afsgroups",
                ),
                c.Link(
                    components=[c.Text(text="Security Group")],
                    on_click=GoToEvent(url="/secgroups"),
                    active="startswith:/secgroups",
                ),
            ],
        ),
        c.Page(components=components),
    ]


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

    print(options)
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
    return layout(
        c.ModelForm(model=User, submit_url="/api/users"), title="Add New User"
    )
    # return [c.Page(components=[c.ModelForm(model=User, submit_url="/api/users")])] # , title="Add New User"),


@router.post("/api/users", response_model=FastUI)
def user_post(
    form: Annotated[User, fastui_form(User)],
    samdb: Annotated[SamDB, Depends(get_smb)],
) -> list[AnyComponent]:
    try:
        user = users.add_user(samdb, form)
    except LdbError as e:
        raise HTTPException(status_code=401, detail=str(e))
    return [form]


@router.get("/api/afsmounts", response_model=FastUI, response_model_exclude_none=True)
async def get_afsmounts():
    return layout(
        c.ModelForm(model=AutoFSMount, submit_url="/api/afsmounts"),
        title="Add New Mount to AutoFS",
    )


@router.post("/api/afsmounts", response_model=FastUI)
async def post_afsmounts(
    form: Annotated[AutoFSMount, fastui_form(AutoFSMount)],
    samdb: Annotated[SamDB, Depends(get_smb)],
) -> list[AnyComponent]:
    try:
        mount = autofs.addAutofsEntry(samdb, form)
    except LdbError as e:
        raise HTTPException(status_code=401, detail=str(e))
    return [form]


@router.get("/api/afsgroups", response_model=FastUI, response_model_exclude_none=True)
async def get_afsgroups():
    return layout(
        c.ModelForm(model=AutoFSGroup, submit_url="/api/afsgroups"),
        title="Add New AutoFS Group",
    )


@router.post("/api/afsgroups")
async def post_afsgroups(
    form: Annotated[AutoFSGroup, fastui_form(AutoFSGroup)],
    samdb: Annotated[SamDB, Depends(get_smb)],
) -> list[AnyComponent]:
    try:
        groups = autofs.addAutofsGroup(data)
    except LdbError as e:
        raise HTTPException(status_code=401, detail=str(e))

    return [form]


@router.get("/api/secgroups", response_model=FastUI, response_model_exclude_none=True)
async def get_secgroups():
    return layout(
        c.ModelForm(model=SecurityGroup, submit_url="/api/secgroups"),
        title="Create New Security Group",
    )


@router.post("/api/secgroups", response_model=FastUI)
async def post_secgroups(
    form: Annotated[SecurityGroup, fastui_form(SecurityGroup)],
    samdb: Annotated[SamDB, Depends(get_smb)],
) -> list[AnyComponent]:
    try:
        group = groups.add_sec_group(data)
    except LdbError as e:
        raise HTTPException(status_code=401, detail=str(e))
    return [form]


@router.get("/")
async def index():
    # Redirect to /docs (relative URL)
    return RedirectResponse(url="/users", status_code=status.HTTP_302_FOUND)

# IMPORTANT: This route should be the last route in this file!!!!!!!
@router.get("/{path:path}")
def root() -> HTMLResponse:
    """Simple HTML page which serves the React app, comes last as it matches all paths."""
    return HTMLResponse(prebuilt_html(title="Guam"))
