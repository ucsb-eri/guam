from pydantic import BaseModel, Field


class SecurityGroup(BaseModel):
    groupname: str = Field(title="Username")
    groupdesc: str = Field(title="Description")
