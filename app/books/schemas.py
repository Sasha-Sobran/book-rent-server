from pydantic import BaseModel, Field


class BookCreate(BaseModel):
    title: str
    author: str
    price: float = Field(ge=0)
    publish_year: str
    quantity: int = Field(ge=0)
    library_id: int
    category_ids: list[int] | None = None
    genre_ids: list[int] | None = None
    new_categories: list[str] | None = None
    new_genres: list[str] | None = None


class BookUpdate(BaseModel):
    title: str | None = None
    author: str | None = None
    price: float | None = Field(default=None, ge=0)
    publish_year: str | None = None
    quantity: int | None = Field(default=None, ge=0)
    library_id: int | None = None
    category_ids: list[int] | None = None
    genre_ids: list[int] | None = None
    new_categories: list[str] | None = None
    new_genres: list[str] | None = None


class BookResponse(BaseModel):
    id: int
    title: str
    author: str
    price: float
    publish_year: str
    quantity: int
    library_id: int
    library_name: str | None = None
    categories: list[str] = []
    genres: list[str] = []

