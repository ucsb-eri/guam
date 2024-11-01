from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from app import config
from app.utils import users, groups, autofs
from typing import Annotated
from fastapi.responses import RedirectResponse

from app.models.user import User
from app.models.autofs import AutoFSMount, AutoFSGroup
from app.models.secgroup import SecurityGroup

templates = Jinja2Templates(directory="app/templates/")

router = APIRouter()


@router.get("/")
async def get_index(request: Request):
    return templates.TemplateResponse("index.html.j2", {"request": request})


# @router.get("/result")
# async def get_result(request: Request):
#     print(request.)
#     return templates.TemplateResponse("result.html.j2", {"request": request})


@router.get("/users")
async def get_user(request: Request):
    # print("request")
    # print(await request.json())
    departmentlist: list[str] = config.departmentlist
    afsserverlist: list[str] = config.afsserverlist
    afsusergroups: list[str] = autofs.afsusergroups()
    secgrouplist: list[str] = list(groups.secgroups().keys())
    secgrouplist.sort(key=str.casefold)

    return templates.TemplateResponse(
        "users.html.j2",
        {
            "request": request,
            "departmentlist": departmentlist,
            "afsserverlist": afsserverlist,
            "afsusergroups": afsusergroups,
            "secgrouplist": secgrouplist,
        },
    )


@router.post("/users")
async def post_user(data: Annotated[User, Form()], request: Request):
    user = users.addUser(data)

    # Error should be handled here!
    return templates.TemplateResponse(
        "result.html.j2", {"request": request, "type": "User", "data": user}
    )

@router.get("/autofs_mounts")
async def get_autofs_mount(request: Request):
    afsgroups: list[str] = autofs.afsusergroups()

    return templates.TemplateResponse(
        "autofs_mounts.html.j2", {"request": request, "afsgroups": afsgroups}
    )


@router.post("/autofs_mounts")
async def post_autofs_mount(data: Annotated[AutoFSMount, Form()], request: Request):
    mount = autofs.addAutofsEntry(data)

    return templates.TemplateResponse(
        "result.html.j2", {"request": request, "type": "AutoFS Mount", "data": mount}
    )

@router.get("/autofs_groups")
async def get_autofs_groups(request: Request):
    return templates.TemplateResponse("autofs_groups.html.j2", {"request": request})


@router.post("/autofs_groups")
async def post_autofs_groups(data: Annotated[AutoFSGroup, Form()], request: Request):
    groups = autofs.addAutofsGroup(data)

    return templates.TemplateResponse(
        "result.html.j2", {"request": request, "type": "AutoFS Group", "data": groups}
    )

@router.get("/secgroups")
async def get_sec_group(request: Request):
    return templates.TemplateResponse("secgroups.html.j2", {"request": request})


@router.post("/secgroups")
async def post_sec_group(data: Annotated[SecurityGroup, Form()], request: Request):
    group = groups.add_sec_group(data)
    # result = addUser(form_data, usersecgroup, afsusergroup)

    return templates.TemplateResponse(
        "result.html.j2", {"request": request, "type": "Security Group", "data": group}
    )

@router.get("/manage_autofs_groups")
async def get_manage_autofs_groups(request: Request):
    return templates.TemplateResponse(
        "manage_autofs_groups.html.j2", {"request": request}
    )


@router.post("/manage_autofs_groups")
async def post_manage_autofs_groups(request: Request):
    # result = addUser(form_data, usersecgroup, afsusergroup)

    return templates.TemplateResponse("result.html.j2")
