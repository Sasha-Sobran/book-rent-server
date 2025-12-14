from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.common.dependencies import LibrarianUserDep, SessionDep, UserDep
from app.rents.controllers import (
    cancel_rent,
    create_rent,
    create_rent_order,
    decline_rent,
    get_rent,
    issue_rent,
    list_rents,
    return_rent,
)
from app.rents.schemas import RentCreate, RentOrderCreate
from app.event_log.decorators import audit_log
from app.models.rent import Rent

rents_router = APIRouter(prefix="/rents", tags=["rents"])


@rents_router.get("/")
async def list_rents_route(
    session: SessionDep,
    user: LibrarianUserDep,
    reader_id: int | None = None,
    status: str | None = None,
):
    return list_rents(
        session,
        librarian_user_id=user["user_id"],
        reader_id=reader_id,
        status_name=status,
    )


@rents_router.get("/my/")
async def my_rents_route(
    session: SessionDep,
    user: UserDep,
    status: str | None = None,
):
    return list_rents(session, reader_user_id=user["user_id"], status_name=status)


@rents_router.get("/{rent_id}/")
async def get_rent_route(rent_id: int, session: SessionDep, user: LibrarianUserDep):
    rent = get_rent(session, rent_id)
    if not rent:
        raise HTTPException(status_code=404, detail="Rent not found")
    return rent


@rents_router.post("/")
@audit_log(
    action_type="create",
    entity_type="rent",
    get_entity_id=lambda result, *args, **kwargs: result.id if result else None,
    get_description=lambda result, *args, **kwargs: (
        f"Створено рент для книги '{result.book_title}' читачу '{result.reader_name}'"
        if result
        else None
    ),
    get_new_values=lambda result, *args, **kwargs: (
        {
            "book_id": result.book_id,
            "book_title": result.book_title,
            "reader_id": result.reader_id,
            "reader_name": result.reader_name,
            "rent_price": result.rent_price,
            "status": result.status,
        }
        if result
        else None
    ),
)
async def create_rent_route(
    data: RentCreate, session: SessionDep, user: LibrarianUserDep
):
    return create_rent(session, data, librarian_user_id=user["user_id"])


@rents_router.post("/request/")
@audit_log(
    action_type="create",
    entity_type="rent_order",
    get_entity_id=lambda result, *args, **kwargs: result.id if result else None,
    get_description=lambda result, *args, **kwargs: (
        f"Створено замовлення на рент книги '{result.book_title}'" if result else None
    ),
    get_new_values=lambda result, *args, **kwargs: (
        {
            "book_id": result.book_id,
            "book_title": result.book_title,
            "status": result.status,
            "rent_price": result.rent_price,
        }
        if result
        else None
    ),
)
async def create_rent_order_route(
    data: RentOrderCreate, session: SessionDep, user: UserDep
):
    return create_rent_order(
        session, data.book_id, data.loan_days, user_id=user["user_id"]
    )


@rents_router.post("/{rent_id}/return/")
@audit_log(
    action_type="update",
    entity_type="rent",
    get_entity_id=lambda result, rent_id, *args, **kwargs: (
        result.id if result else rent_id
    ),
    get_description=lambda result, rent_id, *args, **kwargs: (
        f"Повернено книгу '{result.book_title}'"
        if result
        else f"Повернено рент (ID: {rent_id})"
    ),
    get_old_values=lambda result, session, rent_id, *args, **kwargs: (
        {
            "status": rent.status,
            "return_date": None,
        }
        if session and (rent := session.get(Rent, rent_id))
        else None
    ),
    get_new_values=lambda result, *args, **kwargs: (
        {
            "status": result.status,
            "return_date": (
                result.return_date.isoformat() if result.return_date else None
            ),
        }
        if result
        else None
    ),
)
async def return_rent_route(rent_id: int, session: SessionDep, user: LibrarianUserDep):
    rent = return_rent(session, rent_id, librarian_user_id=user["user_id"])
    if not rent:
        raise HTTPException(status_code=404, detail="Rent not found")
    return rent


@rents_router.post("/{rent_id}/issue/")
@audit_log(
    action_type="update",
    entity_type="rent",
    get_entity_id=lambda result, rent_id, *args, **kwargs: (
        result.id if result else rent_id
    ),
    get_description=lambda result, rent_id, *args, **kwargs: (
        f"Видано книгу '{result.book_title}' читачу '{result.reader_name}'"
        if result
        else f"Видано рент (ID: {rent_id})"
    ),
    get_old_values=lambda result, session, rent_id, *args, **kwargs: (
        {
            "status": rent.status,
        }
        if session and (rent := session.get(Rent, rent_id))
        else None
    ),
    get_new_values=lambda result, *args, **kwargs: (
        {
            "status": result.status,
        }
        if result
        else None
    ),
)
async def issue_rent_route(rent_id: int, session: SessionDep, user: LibrarianUserDep):
    rent = issue_rent(session, rent_id, librarian_user_id=user["user_id"])
    if not rent:
        raise HTTPException(status_code=404, detail="Rent not found")
    return rent


@rents_router.post("/{rent_id}/decline/")
@audit_log(
    action_type="update",
    entity_type="rent",
    get_entity_id=lambda result, rent_id, *args, **kwargs: (
        result.id if result else rent_id
    ),
    get_description=lambda result, rent_id, *args, **kwargs: (
        f"Відхилено замовлення на рент книги '{result.book_title}'"
        if result
        else f"Відхилено рент (ID: {rent_id})"
    ),
    get_old_values=lambda result, session, rent_id, *args, **kwargs: (
        {
            "status": rent.status,
        }
        if session and (rent := session.get(Rent, rent_id))
        else None
    ),
    get_new_values=lambda result, *args, **kwargs: (
        {
            "status": result.status,
        }
        if result
        else None
    ),
)
async def decline_rent_route(rent_id: int, session: SessionDep, user: LibrarianUserDep):
    rent = decline_rent(session, rent_id, librarian_user_id=user["user_id"])
    if not rent:
        raise HTTPException(status_code=404, detail="Rent not found")
    return rent


@rents_router.post("/{rent_id}/cancel/")
@audit_log(
    action_type="update",
    entity_type="rent",
    get_entity_id=lambda result, rent_id, *args, **kwargs: (
        result.id if result else rent_id
    ),
    get_description=lambda result, rent_id, *args, **kwargs: (
        f"Скасовано замовлення на рент книги '{result.book_title}'"
        if result
        else f"Скасовано рент (ID: {rent_id})"
    ),
    get_old_values=lambda result, session, rent_id, *args, **kwargs: (
        {
            "status": rent.status,
        }
        if session and (rent := session.get(Rent, rent_id))
        else None
    ),
    get_new_values=lambda result, *args, **kwargs: (
        {
            "status": result.status,
        }
        if result
        else None
    ),
)
async def cancel_rent_route(rent_id: int, session: SessionDep, user: UserDep):
    rent = cancel_rent(session, rent_id, user_id=user["user_id"])
    if not rent:
        raise HTTPException(status_code=404, detail="Rent not found")
    return rent
