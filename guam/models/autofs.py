from typing import Annotated

from fastui.forms import Textarea
from pydantic import BaseModel, Field, field_validator


class AutoFSMount(BaseModel):
    afsgroups: list[str] = Field(
        title="AutoFS Groups",
        json_schema_extra={"search_url": "/api/forms/afsgroups"},
    )
    autofspath: str = Field(title="AutoFS Path")
    autofsmountpoint: str = Field(title="AutoFS local mountpoint")

    @field_validator("afsgroups", mode="before")
    @classmethod
    def correct_select_multiple(cls, v: list[str]) -> list[str]:
        if isinstance(v, list):
            return v
        else:
            return [v]


class AutoFSGroup(BaseModel):
    groups: Annotated[str | None, Textarea(rows=5)] = Field(
        title="AutoFS Groups", placeholder="Group names, one per line"
    )


class AutoFSFilesystem(BaseModel):
    username: str = Field(title="Username")
    create_mount: bool | None = Field(
        None,
        title="Create Mount",
        description="If this is disabled, the AutoFS Server field below will be ignored",
        json_schema_extra={"mode": "switch"},
    )

    afsserver: Annotated[str, None] = Field(
        title="AutoFS Server",
        json_schema_extra={"search_url": "/api/forms/servers"},
        default=None,
    )
