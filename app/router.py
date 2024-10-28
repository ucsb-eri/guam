from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates/")

router = APIRouter()


@router.get("/")
async def get_index(request: Request):
    return templates.TemplateResponse("index.html.j2", {"request": request})

@router.get("/users")
async def get_user(request: Request):
    return templates.TemplateResponse("users.html.j2", {"request": request})

@router.post("/users")
async def post_user(request: Request):
    result = addUser(form_data, usersecgroup, afsusergroup)

    return templates.TemplateResponse('result.html.j2')

@router.get("/autofs_entries")
async def get_autofs_entry(request: Request):
    return templates.TemplateResponse("autofs_entries.html.j2", {"request": request})

@router.post("/autofs_entries")
async def post_autofs_entry(request: Request):
    result = addUser(form_data, usersecgroup, afsusergroup)

    return templates.TemplateResponse('result.html.j2')

@router.get("/autofs_groups")
async def get_autofs_entry(request: Request):
    return templates.TemplateResponse("autofs_groups.html.j2", {"request": request})

@router.post("/autofs_groups")
async def post_autofs_entry(request: Request):
    result = addUser(form_data, usersecgroup, afsusergroup)

    return templates.TemplateResponse('result.html.j2')

@router.get("/autofs_mounts")
async def get_autofs_mount(request: Request):
    return templates.TemplateResponse("autofs_mounts.html.j2", {"request": request})

@router.post("/autofs_mounts")
async def post_autofs_mount(request: Request):
    result = addUser(form_data, usersecgroup, afsusergroup)

    return templates.TemplateResponse('result.html.j2')

@router.get("/secgroups")
async def get_sec_group(request: Request):
    return templates.TemplateResponse("secgroups.html.j2", {"request": request})

@router.post("/secgroups")
async def post_sec_group(request: Request):
    result = addUser(form_data, usersecgroup, afsusergroup)

    return templates.TemplateResponse('result.html.j2')

@router.get("/manage_autofs_groups")
async def get_manage_autofs_groups(request: Request):
    return templates.TemplateResponse("manage_autofs_groups.html.j2", {"request": request})

@router.post("/manage_autofs_groups")
async def post_manage_autofs_groups(request: Request):
    result = addUser(form_data, usersecgroup, afsusergroup)

    return templates.TemplateResponse('result.html.j2')
