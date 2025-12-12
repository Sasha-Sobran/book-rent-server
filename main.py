from fastapi import FastAPI
from sqlmodel import SQLModel
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def include_routers():
    from app.user.router import user_router
    from app.admin.router import admin_router
    from app.common.routers import common_router
    from app.settings.router import settings_router
    from app.readers.router import readers_router
    from app.books.router import books_router
    from app.libraries.router import libraries_router
    from app.rents.router import rents_router

    app.include_router(user_router)
    app.include_router(admin_router)
    app.include_router(common_router)
    app.include_router(settings_router)
    app.include_router(readers_router)
    app.include_router(books_router)
    app.include_router(libraries_router)
    app.include_router(rents_router)


def create_tables():
    from app import models
    from database import engine

    
    SQLModel.metadata.create_all(engine)
    


create_tables()
include_routers()


