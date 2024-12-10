from pydantic import BaseModel, Field


class SecurityGroup(BaseModel):
    groupname: str = Field(title="Group Name")
    groupdesc: str = Field(title="Description")
