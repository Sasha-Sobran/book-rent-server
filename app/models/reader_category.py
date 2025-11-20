from sqlmodel import Field, Relationship, SQLModel


class ReaderCategory(SQLModel, table=True):
    __tablename__ = "reader_category"

    id: int = Field(default=None, primary_key=True)
    name: str = Field(unique=True)
    discount_percentage: int = Field(ge=0, le=100)

    readers: list["Reader"] = Relationship(back_populates="reader_category")