from pydantic import BaseModel


class CreateReaderRequest(BaseModel):
    name: str
    surname: str
    phone_number: str | None = None
    address: str | None = None
    reader_category_id: int | None = None
    user_id: int | None = None


class UpdateReaderRequest(BaseModel):
    name: str | None = None
    surname: str | None = None
    phone_number: str | None = None
    address: str | None = None
    reader_category_id: int | None = None


class ReaderResponse(BaseModel):
    id: int
    name: str
    surname: str
    phone_number: str | None
    address: str | None
    reader_category_id: int | None
    reader_category_name: str | None
    user_id: int | None
    user_email: str | None
