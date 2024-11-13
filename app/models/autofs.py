from pydantic import BaseModel, Field, field_validator


class AutoFSMount(BaseModel):
    afsgroups: list[str] = Field(
        title="AutoFS Groups",
        json_schema_extra={"search_url": "/api/forms/afsgroups"},
    )
    autofspath: str = Field(title="AutFS Path")
    autofsmountpoint: str = Field(title="AutoFS Mount Point")

    # @field_validator("afsgroup", mode="before")
    # @classmethod
    # def correct_select_multiple(cls, v: list[str]) -> list[str]:
    #     if isinstance(v, list):
    #         return v
    #     else:
    #         return [v]


class AutoFSGroup(BaseModel):
    groups: str = Field(title="AutoFS Groups")
