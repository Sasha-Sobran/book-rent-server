from fastapi import APIRouter, HTTPException

from app.common.dependencies import AdminUserDep, SessionDep
from app.settings.controllers import (
    create_category,
    create_genre,
    create_penalty_type,
    create_reader_category,
    delete_category,
    delete_genre,
    delete_penalty_type,
    delete_reader_category,
    get_penalty_types,
    get_reader_categories,
    update_reader_category,
)

settings_router = APIRouter(prefix="/settings", tags=["settings"])


@settings_router.get("/reader-categories/")
async def get_reader_categories_route(session: SessionDep, user: AdminUserDep):
    return get_reader_categories(session)


@settings_router.get("/penalty-types/")
async def get_penalty_types_route(session: SessionDep, user: AdminUserDep):
    return get_penalty_types(session)


@settings_router.post("/genres/")
async def create_genre_route(name: str, session: SessionDep, user: AdminUserDep):
    return create_genre(session, name)


@settings_router.delete("/genres/{genre_id}/")
async def delete_genre_route(genre_id: int, session: SessionDep, user: AdminUserDep):
    if not delete_genre(session, genre_id):
        raise HTTPException(status_code=404, detail="Genre not found")
    return {"message": "Genre deleted"}


@settings_router.post("/categories/")
async def create_category_route(name: str, session: SessionDep, user: AdminUserDep):
    return create_category(session, name)


@settings_router.delete("/categories/{category_id}/")
async def delete_category_route(category_id: int, session: SessionDep, user: AdminUserDep):
    if not delete_category(session, category_id):
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category deleted"}


@settings_router.post("/reader-categories/")
async def create_reader_category_route(name: str, discount_percentage: int, session: SessionDep, user: AdminUserDep):
    return create_reader_category(session, name, discount_percentage)


@settings_router.put("/reader-categories/{category_id}/")
async def update_reader_category_route(category_id: int, name: str, discount_percentage: int, session: SessionDep, user: AdminUserDep):
    result = update_reader_category(session, category_id, name, discount_percentage)
    if not result:
        raise HTTPException(status_code=404, detail="Category not found")
    return result


@settings_router.delete("/reader-categories/{category_id}/")
async def delete_reader_category_route(category_id: int, session: SessionDep, user: AdminUserDep):
    if not delete_reader_category(session, category_id):
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category deleted"}


@settings_router.post("/penalty-types/")
async def create_penalty_type_route(name: str, session: SessionDep, user: AdminUserDep):
    return create_penalty_type(session, name)


@settings_router.delete("/penalty-types/{type_id}/")
async def delete_penalty_type_route(type_id: int, session: SessionDep, user: AdminUserDep):
    if not delete_penalty_type(session, type_id):
        raise HTTPException(status_code=404, detail="Penalty type not found")
    return {"message": "Penalty type deleted"}
