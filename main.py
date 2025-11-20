from fastapi import FastAPI
from sqlmodel import SQLModel, Session

from app.models.genre import Genre
from app.models.category import Category
from app.schemas.category_schemas import CategoryCreate
from app.schemas.genre_schemas import GenreCreate
from database import engine

db = Session(engine)

app = FastAPI()

def create_tables():
    from app import models

    SQLModel.metadata.create_all(engine)


create_tables()


@app.post("/create_genre")
def create_genre(genre: GenreCreate):
    db.add(Genre(name=genre.name))
    db.commit()
    return genre

@app.get("/get_genres")
def get_genres():
    genres = db.query(Genre).all()
    return genres

@app.post("/create_category")
def create_category(category: CategoryCreate):
    db.add(Category(name=category.name))
    db.commit()
    return category

@app.get("/get_categories")
def get_categories():
    categories = db.query(Category).all()
    return categories