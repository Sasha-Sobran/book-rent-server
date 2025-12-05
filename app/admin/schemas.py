from pydantic import BaseModel

from app.models.role import Role


class CreateRoleRequest(BaseModel):
    name: str


class CreateRoleResponse(BaseModel):
    id: int
    name: str


class CreateAdminRequest(BaseModel):
    email: str
    password: str
    role_id: int
    name: str
    phone_number: str


class CreateLibrarianRequest(BaseModel):
    email: str
    password: str
    role_id: int
    name: str
    phone_number: str