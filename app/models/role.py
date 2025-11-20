from sqlmodel import Field, Relationship, SQLModel

class Role(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str = Field(unique=True)

    users: list["User"] = Relationship(back_populates="role")