from fastapi import APIRouter

from app.common.controllers import quick_select
from app.common.dependencies import SessionDep
from app.models.category import Category
from app.models.genre import Genre
from app.models.reader_category import ReaderCategory
from app.models.role import Role

common_router = APIRouter(prefix="", tags=["common"])


@common_router.get("/health/")
async def health_route():
    return {"status": "ok"}


@common_router.get("/roles/")
async def get_roles_route(session: SessionDep):
    result = await quick_select(session=session, model=Role)
    return result.scalars().all()


@common_router.get("/genres/")
async def get_genres_route(session: SessionDep):
    result = await quick_select(session=session, model=Genre)
    return result.scalars().all()


@common_router.get("/categories/")
async def get_categories_route(session: SessionDep):
    result = await quick_select(session=session, model=Category)
    return result.scalars().all()


@common_router.get("/reader-categories/")
async def get_reader_categories_route(session: SessionDep):
    result = await quick_select(session=session, model=ReaderCategory)
    return result.scalars().all()
