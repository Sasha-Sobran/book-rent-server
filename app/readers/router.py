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

readers_router = APIRouter(prefix="/readers", tags=["readers"])


@readers_router.get("/")
async def get_readers_route(session: SessionDep, user: LibrarianUserDep, query: str | None = None):
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
async def create_reader_route(data: CreateReaderRequest, session: SessionDep, user: LibrarianUserDep):
    return create_reader(session, data)


@readers_router.put("/{reader_id}/")
async def update_reader_route(reader_id: int, data: UpdateReaderRequest, session: SessionDep, user: LibrarianUserDep):
    reader = update_reader(session, reader_id, data)
    if not reader:
        raise HTTPException(status_code=404, detail="Reader not found")
    return reader


@readers_router.delete("/{reader_id}/")
async def delete_reader_route(reader_id: int, session: SessionDep, user: LibrarianUserDep):
    if not delete_reader(session, reader_id):
        raise HTTPException(status_code=404, detail="Reader not found")
    return {"message": "Reader deleted"}

