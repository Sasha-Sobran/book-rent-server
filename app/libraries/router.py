from fastapi import APIRouter
from sqlmodel import select

from app.common.dependencies import AdminUserDep, LibrarianUserDep, SessionDep, UserDep
from app.libraries.controllers import (
    create_city,
    create_library,
    list_cities,
    list_libraries,
    _to_response,
)
from app.libraries.schemas import CityCreate, LibraryCreate
from app.models.librarian import Librarian

libraries_router = APIRouter(prefix="/libraries", tags=["libraries"])


@libraries_router.get("/")
async def list_libraries_route(session: SessionDep, user: UserDep):
    return list_libraries(session)


@libraries_router.get("/me/")
async def my_library_route(session: SessionDep, user: LibrarianUserDep):
    result = session.exec(select(Librarian).where(Librarian.user_id == user["user_id"]))
    librarian = result.first()
    if not librarian:
        return None
    if not librarian.library:
        session.refresh(librarian, attribute_names=["library"])
    return _to_response(librarian.library)


@libraries_router.post("/")
async def create_library_route(data: LibraryCreate, session: SessionDep):
    return create_library(session, data)


@libraries_router.get("/cities/")
async def list_cities_route(session: SessionDep, user: UserDep):
    return list_cities(session)


@libraries_router.post("/cities/")
async def create_city_route(data: CityCreate, session: SessionDep):
    return create_city(session, data)

