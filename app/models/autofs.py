from pydantic import BaseModel


class AutoFSMount(BaseModel):
    afsgroups: list[str]
    autofspath: str
    autofsmountpoint: str


class AutoFSGroup(BaseModel):
    groups: str

