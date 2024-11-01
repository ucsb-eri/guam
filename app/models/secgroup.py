from pydantic import BaseModel


class SecurityGroup(BaseModel):
    groupname: str
    groupdesc: str
