from pydantic import BaseModel


class LibraryCreate(BaseModel):
    name: str
    city_id: int
    address: str
    phone_number: str


class LibraryResponse(BaseModel):
    id: int
    name: str
    city_id: int
    city_name: str | None = None
    address: str
    phone_number: str


class CityCreate(BaseModel):
    name: str


class CityResponse(BaseModel):
    id: int
    name: str
