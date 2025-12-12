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
async def create_rent_route(data: RentCreate, session: SessionDep, user: LibrarianUserDep):
    return create_rent(session, data, librarian_user_id=user["user_id"])


@rents_router.post("/request/")
async def create_rent_order_route(data: RentOrderCreate, session: SessionDep, user: UserDep):
    return create_rent_order(session, data.book_id, data.loan_days, user_id=user["user_id"])


@rents_router.post("/{rent_id}/return/")
async def return_rent_route(
    rent_id: int, session: SessionDep, user: LibrarianUserDep
):
    rent = return_rent(session, rent_id, librarian_user_id=user["user_id"])
    if not rent:
        raise HTTPException(status_code=404, detail="Rent not found")
    return rent


@rents_router.post("/{rent_id}/issue/")
async def issue_rent_route(rent_id: int, session: SessionDep, user: LibrarianUserDep):
    rent = issue_rent(session, rent_id, librarian_user_id=user["user_id"])
    if not rent:
        raise HTTPException(status_code=404, detail="Rent not found")
    return rent


@rents_router.post("/{rent_id}/decline/")
async def decline_rent_route(rent_id: int, session: SessionDep, user: LibrarianUserDep):
    rent = decline_rent(session, rent_id, librarian_user_id=user["user_id"])
    if not rent:
        raise HTTPException(status_code=404, detail="Rent not found")
    return rent


@rents_router.post("/{rent_id}/cancel/")
async def cancel_rent_route(rent_id: int, session: SessionDep, user: UserDep):
    rent = cancel_rent(session, rent_id, user_id=user["user_id"])
    if not rent:
        raise HTTPException(status_code=404, detail="Rent not found")
    return rent


