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


def user_created():
    return layout(
        [
            c.Page(  # Page provides a basic container for components
                components=[
                    # renders `<h2>Users</h2>`
                    c.Heading(text="Users", level=2),
                    c.Table(
                        data=users,
                        # define two columns for the table
                        columns=[
                            # the first is the users, name rendered as a link to their profile
                            DisplayLookup(
                                field="name", on_click=GoToEvent(url="/user/{id}/")
                            ),
                            # the second is the date of birth, rendered as a date
                            DisplayLookup(field="dob", mode=DisplayMode.date),
                        ],
                    ),
                ]
            ),
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
