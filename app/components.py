from fastui import AnyComponent
from fastui import components as c
from fastui.events import GoToEvent


def layout(*components: AnyComponent, title: str) -> list[AnyComponent]:
    return [
        c.PageTitle(text=title),
        c.Navbar(
            title="GUAM",
            title_event=GoToEvent(url="/users"),
            start_links=[
                c.Link(
                    components=[c.Text(text="User")],
                    on_click=GoToEvent(url="/users"),
                    active="startswith:/users",
                ),
                c.Link(
                    components=[c.Text(text="AFS Mount")],
                    on_click=GoToEvent(url="/afsmounts"),
                    active="startswith:/afsmounts",
                ),
                c.Link(
                    components=[c.Text(text="AFS Group")],
                    on_click=GoToEvent(url="/afsgroups"),
                    active="startswith:/afsgroups",
                ),
                c.Link(
                    components=[c.Text(text="Security Group")],
                    on_click=GoToEvent(url="/secgroups"),
                    active="startswith:/secgroups",
                ),
            ],
        ),
        c.Page(components=components),
    ]


def user_created(user):
    return layout(
        components=[
            c.Markdown(f"""
                   <table>
                   <tr><td>Username</td><td>{user.username}</td></tr>
                   </table>
            """)
        ],
        title="User Added",
    )


#
# Username￼
# First Name￼
# Last Name￼
# Email￼
# Description￼
# User Department
# Select...
# ￼
# ￼
# User AutoFS Server
# Select...
# ￼
# ￼
# AutoFS Groups
# Select...
# ￼
# ￼
# Primary AD Group
# Select...
# ￼
# ￼
# Additional AD Groups
