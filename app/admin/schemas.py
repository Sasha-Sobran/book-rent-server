from pydantic import BaseModel

from app.models.role import Role


class CreateRoleRequest(BaseModel):
    name: str


class CreateRoleResponse(BaseModel):
    id: int
    name: str


class CreateLibrarianRequest(BaseModel):
    email: str
    password: str
    name: str
    surname: str
    phone_number: str | None = None
    library_id: int


class EditUserRequest(BaseModel):
    email: str
    password: str | None = None
    role_id: int
    name: str
    surname: str
    phone_number: str | None = None
