from sqlmodel import Field, Relationship, SQLModel

class BookCategory(SQLModel, table=True):
    __tablename__ = "book_categories"

    book_id: int = Field(foreign_key="book.id", primary_key=True)
    category_id: int = Field(foreign_key="category.id", primary_key=True)

class BookGenre(SQLModel, table=True):
    __tablename__ = "book_genres"
    
    book_id: int = Field(foreign_key="book.id", primary_key=True)
    genre_id: int = Field(foreign_key="genre.id", primary_key=True)

class Book(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    title: str
    price: float
    publish_year: str
    author: str
    library_id: int = Field(foreign_key="library.id")
    quantity: int

    library: "Library" = Relationship(back_populates="books")
    rents: list["Rent"] = Relationship(back_populates="book")
    categories: list["Category"] = Relationship(back_populates="books", link_model=BookCategory)
    genres: list["Genre"] = Relationship(back_populates="books", link_model=BookGenre)


