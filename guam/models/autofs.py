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
