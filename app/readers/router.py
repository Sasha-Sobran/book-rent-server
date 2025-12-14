from fastapi import APIRouter, HTTPException

from app.common.dependencies import SessionDep, LibrarianUserDep
from app.readers.controllers import (
    create_reader,
    delete_reader,
    get_all_readers,
    get_reader_by_id,
    search_readers,
    update_reader,
)
from app.readers.schemas import CreateReaderRequest, UpdateReaderRequest
from app.event_log.decorators import audit_log
from app.models.reader import Reader

readers_router = APIRouter(prefix="/readers", tags=["readers"])


@readers_router.get("/")
async def get_readers_route(
    session: SessionDep, user: LibrarianUserDep, query: str | None = None
):
    if query:
        return search_readers(session, query)
    return get_all_readers(session)


@readers_router.get("/{reader_id}/")
async def get_reader_route(reader_id: int, session: SessionDep, user: LibrarianUserDep):
    reader = get_reader_by_id(session, reader_id)
    if not reader:
        raise HTTPException(status_code=404, detail="Reader not found")
    return reader


@readers_router.post("/")
@audit_log(
    action_type="create",
    entity_type="reader",
    get_entity_id=lambda result, *args, **kwargs: result.id if result else None,
    get_description=lambda result, *args, **kwargs: (
        f"Створено читача '{result.name} {result.surname}'" if result else None
    ),
    get_new_values=lambda result, *args, **kwargs: (
        {
            "name": result.name,
            "surname": result.surname,
            "phone_number": result.phone_number,
            "address": result.address,
            "reader_category_id": result.reader_category_id,
            "user_id": result.user_id,
        }
        if result
        else None
    ),
)
async def create_reader_route(
    data: CreateReaderRequest, session: SessionDep, user: LibrarianUserDep
):
    return create_reader(session, data)


@readers_router.put("/{reader_id}/")
@audit_log(
    action_type="update",
    entity_type="reader",
    get_entity_id=lambda result, reader_id, *args, **kwargs: (
        result.id if result else reader_id
    ),
    get_description=lambda result, reader_id, *args, **kwargs: (
        f"Оновлено читача '{result.name} {result.surname}'"
        if result
        else f"Оновлено читача (ID: {reader_id})"
    ),
    get_old_values=lambda result, session, reader_id, *args, **kwargs: (
        {
            "name": old_reader.name,
            "surname": old_reader.surname,
            "phone_number": old_reader.phone_number,
            "address": old_reader.address,
            "reader_category_id": old_reader.reader_category_id,
        }
        if session and (old_reader := session.get(Reader, reader_id))
        else None
    ),
    get_new_values=lambda result, *args, **kwargs: (
        {
            "name": result.name,
            "surname": result.surname,
            "phone_number": result.phone_number,
            "address": result.address,
            "reader_category_id": result.reader_category_id,
        }
        if result
        else None
    ),
)
async def update_reader_route(
    reader_id: int,
    data: UpdateReaderRequest,
    session: SessionDep,
    user: LibrarianUserDep,
):
    reader = update_reader(session, reader_id, data)
    if not reader:
        raise HTTPException(status_code=404, detail="Reader not found")
    return reader


@readers_router.delete("/{reader_id}/")
@audit_log(
    action_type="delete",
    entity_type="reader",
    get_entity_id=lambda result, reader_id, *args, **kwargs: reader_id,
    get_description=lambda result, session, reader_id, *args, **kwargs: (
        f"Видалено читача '{reader.name} {reader.surname}'"
        if session and (reader := session.get(Reader, reader_id))
        else f"Видалено читача (ID: {reader_id})"
    ),
    get_old_values=lambda result, session, reader_id, *args, **kwargs: (
        {
            "name": reader.name,
            "surname": reader.surname,
            "phone_number": reader.phone_number,
            "user_id": reader.user_id,
        }
        if session and (reader := session.get(Reader, reader_id))
        else None
    ),
)
async def delete_reader_route(
    reader_id: int, session: SessionDep, user: LibrarianUserDep
):
    if not delete_reader(session, reader_id):
        raise HTTPException(status_code=404, detail="Reader not found")
    return {"message": "Reader deleted"}
