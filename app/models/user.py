from pydantic import BaseModel

class User(BaseModel):
    username: str
    fname: str
    lname: str
    email: str
    description: str
    department: str
    userafsserver: str
    afsusergroup: list[str]
    userprimarygroup: str
    usersecgroup: list[str]
