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
from app.event_log.decorators import audit_log
from app.models.genre import Genre
from app.models.category import Category
from app.models.reader_category import ReaderCategory
from app.models.penalty_type import PenaltyType

settings_router = APIRouter(prefix="/settings", tags=["settings"])


@settings_router.get("/reader-categories/")
async def get_reader_categories_route(session: SessionDep, user: AdminUserDep):
    return get_reader_categories(session)


@settings_router.get("/penalty-types/")
async def get_penalty_types_route(session: SessionDep, user: AdminUserDep):
    return get_penalty_types(session)


@settings_router.post("/genres/")
@audit_log(
    action_type="create",
    entity_type="genre",
    get_entity_id=lambda result, *args, **kwargs: result.id if result else None,
    get_description=lambda result, name, *args, **kwargs: (
        f"Створено жанр '{name}'" if result else None
    ),
    get_new_values=lambda result, name, *args, **kwargs: (
        {
            "name": name,
        }
        if result
        else None
    ),
)
async def create_genre_route(name: str, session: SessionDep, user: AdminUserDep):
    return create_genre(session, name)


@settings_router.delete("/genres/{genre_id}/")
@audit_log(
    action_type="delete",
    entity_type="genre",
    get_entity_id=lambda result, genre_id, *args, **kwargs: genre_id,
    get_description=lambda result, session, genre_id, *args, **kwargs: (
        f"Видалено жанр '{genre.name}'"
        if session and (genre := session.get(Genre, genre_id))
        else f"Видалено жанр (ID: {genre_id})"
    ),
    get_old_values=lambda result, session, genre_id, *args, **kwargs: (
        {
            "name": genre.name,
        }
        if session and (genre := session.get(Genre, genre_id))
        else None
    ),
)
async def delete_genre_route(genre_id: int, session: SessionDep, user: AdminUserDep):
    if not delete_genre(session, genre_id):
        raise HTTPException(status_code=404, detail="Genre not found")
    return {"message": "Genre deleted"}


@settings_router.post("/categories/")
@audit_log(
    action_type="create",
    entity_type="category",
    get_entity_id=lambda result, *args, **kwargs: result.id if result else None,
    get_description=lambda result, name, *args, **kwargs: (
        f"Створено категорію '{name}'" if result else None
    ),
    get_new_values=lambda result, name, *args, **kwargs: (
        {
            "name": name,
        }
        if result
        else None
    ),
)
async def create_category_route(name: str, session: SessionDep, user: AdminUserDep):
    return create_category(session, name)


@settings_router.delete("/categories/{category_id}/")
@audit_log(
    action_type="delete",
    entity_type="category",
    get_entity_id=lambda result, category_id, *args, **kwargs: category_id,
    get_description=lambda result, session, category_id, *args, **kwargs: (
        f"Видалено категорію '{category.name}'"
        if session and (category := session.get(Category, category_id))
        else f"Видалено категорію (ID: {category_id})"
    ),
    get_old_values=lambda result, session, category_id, *args, **kwargs: (
        {
            "name": category.name,
        }
        if session and (category := session.get(Category, category_id))
        else None
    ),
)
async def delete_category_route(
    category_id: int, session: SessionDep, user: AdminUserDep
):
    if not delete_category(session, category_id):
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category deleted"}


@settings_router.post("/reader-categories/")
@audit_log(
    action_type="create",
    entity_type="reader_category",
    get_entity_id=lambda result, *args, **kwargs: result.id if result else None,
    get_description=lambda result, name, *args, **kwargs: (
        f"Створено категорію читача '{name}'" if result else None
    ),
    get_new_values=lambda result, name, discount_percentage, *args, **kwargs: (
        {
            "name": name,
            "discount_percentage": discount_percentage,
        }
        if result
        else None
    ),
)
async def create_reader_category_route(
    name: str, discount_percentage: int, session: SessionDep, user: AdminUserDep
):
    return create_reader_category(session, name, discount_percentage)


@settings_router.put("/reader-categories/{category_id}/")
@audit_log(
    action_type="update",
    entity_type="reader_category",
    get_entity_id=lambda result, category_id, *args, **kwargs: (
        result.id if result else category_id
    ),
    get_description=lambda result, category_id, *args, **kwargs: (
        f"Оновлено категорію читача '{result.name}'"
        if result
        else f"Оновлено категорію читача (ID: {category_id})"
    ),
    get_old_values=lambda result, session, category_id, *args, **kwargs: (
        {
            "name": old_category.name,
            "discount_percentage": old_category.discount_percentage,
        }
        if session and (old_category := session.get(ReaderCategory, category_id))
        else None
    ),
    get_new_values=lambda result, name, discount_percentage, *args, **kwargs: (
        {
            "name": name,
            "discount_percentage": discount_percentage,
        }
        if result
        else None
    ),
)
async def update_reader_category_route(
    category_id: int,
    name: str,
    discount_percentage: int,
    session: SessionDep,
    user: AdminUserDep,
):
    result = update_reader_category(session, category_id, name, discount_percentage)
    if not result:
        raise HTTPException(status_code=404, detail="Category not found")
    return result


@settings_router.delete("/reader-categories/{category_id}/")
@audit_log(
    action_type="delete",
    entity_type="reader_category",
    get_entity_id=lambda result, category_id, *args, **kwargs: category_id,
    get_description=lambda result, session, category_id, *args, **kwargs: (
        f"Видалено категорію читача '{category.name}'"
        if session and (category := session.get(ReaderCategory, category_id))
        else f"Видалено категорію читача (ID: {category_id})"
    ),
    get_old_values=lambda result, session, category_id, *args, **kwargs: (
        {
            "name": category.name,
            "discount_percentage": category.discount_percentage,
        }
        if session and (category := session.get(ReaderCategory, category_id))
        else None
    ),
)
async def delete_reader_category_route(
    category_id: int, session: SessionDep, user: AdminUserDep
):
    if not delete_reader_category(session, category_id):
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category deleted"}


@settings_router.post("/penalty-types/")
@audit_log(
    action_type="create",
    entity_type="penalty_type",
    get_entity_id=lambda result, *args, **kwargs: result.id if result else None,
    get_description=lambda result, name, *args, **kwargs: (
        f"Створено тип штрафу '{name}'" if result else None
    ),
    get_new_values=lambda result, name, *args, **kwargs: (
        {
            "name": name,
        }
        if result
        else None
    ),
)
async def create_penalty_type_route(name: str, session: SessionDep, user: AdminUserDep):
    return create_penalty_type(session, name)


@settings_router.delete("/penalty-types/{type_id}/")
@audit_log(
    action_type="delete",
    entity_type="penalty_type",
    get_entity_id=lambda result, type_id, *args, **kwargs: type_id,
    get_description=lambda result, session, type_id, *args, **kwargs: (
        f"Видалено тип штрафу '{penalty_type.name}'"
        if session and (penalty_type := session.get(PenaltyType, type_id))
        else f"Видалено тип штрафу (ID: {type_id})"
    ),
    get_old_values=lambda result, session, type_id, *args, **kwargs: (
        {
            "name": penalty_type.name,
        }
        if session and (penalty_type := session.get(PenaltyType, type_id))
        else None
    ),
)
async def delete_penalty_type_route(
    type_id: int, session: SessionDep, user: AdminUserDep
):
    if not delete_penalty_type(session, type_id):
        raise HTTPException(status_code=404, detail="Penalty type not found")
    return {"message": "Penalty type deleted"}
