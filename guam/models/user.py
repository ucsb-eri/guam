from pydantic import BaseModel, Field, field_validator


class User(BaseModel):
    username: str = Field(title="Username")
    fname: str = Field(title="First Name")
    lname: str = Field(title="Last Name")
    email: str = Field(title="Email")
    description: str = Field(title="Description", default="")
    department: str = Field(
        title="User Department",
        json_schema_extra={"search_url": "/api/forms/departments"},
    )
    userafsserver: str = Field(
        title="User AutoFS Server",
        json_schema_extra={"search_url": "/api/forms/servers"},
    )
    afsusergroup: list[str] = Field(
        title="AutoFS Groups",
        json_schema_extra={"search_url": "/api/forms/afsgroups"},
        default="",
    )
    userprimarygroup: str = Field(
        title="Primary AD Group",
        json_schema_extra={"search_url": "/api/forms/secgroups"},
    )
    usersecgroup: list[str] = Field(
        title="Additional AD Groups",
        json_schema_extra={"search_url": "/api/forms/secgroups"},
        default="",
    )

    @field_validator("afsusergroup", "usersecgroup", mode="before")
    @classmethod
    def correct_select_multiple(cls, v: list[str]) -> list[str]:
        if isinstance(v, list):
            return v
        else:
            return [v]
