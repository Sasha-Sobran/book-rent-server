from sqlmodel import Field, Relationship, SQLModel


class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    surname: str
    phone_number: None | str = Field(default=None, unique=True)
    email: str = Field(unique=True)
    password: str = Field(min_length=8)
    role_id: int = Field(foreign_key="role.id")

    librarians: list["Librarian"] = Relationship(back_populates="user")
    readers: list["Reader"] = Relationship(back_populates="user")
    role: "Role" = Relationship(back_populates="users")
