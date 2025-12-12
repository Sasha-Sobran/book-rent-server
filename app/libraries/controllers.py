from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.libraries.schemas import CityCreate, CityResponse, LibraryCreate, LibraryResponse
from app.models.city import City
from app.models.library import Library


def list_libraries(session: Session) -> list[LibraryResponse]:
    libs = session.exec(select(Library).join(City)).all()
    return [_to_response(l) for l in libs]


def create_library(session: Session, data: LibraryCreate) -> LibraryResponse:
    _validate_city(session, data.city_id)
    lib = Library(
        name=data.name,
        city_id=data.city_id,
        address=data.address,
        phone_number=data.phone_number,
    )
    session.add(lib)
    session.commit()
    session.refresh(lib)
    return _to_response(lib)


def list_cities(session: Session) -> list[CityResponse]:
    cities = session.exec(select(City)).all()
    return [CityResponse(id=c.id, name=c.name) for c in cities]


def create_city(session: Session, data: CityCreate) -> CityResponse:
    city = City(name=data.name)
    session.add(city)
    session.commit()
    session.refresh(city)
    return CityResponse(id=city.id, name=city.name)


def _validate_city(session: Session, city_id: int):
    city = session.get(City, city_id)
    if city is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="City not found",
        )


def _to_response(library: Library) -> LibraryResponse:
    return LibraryResponse(
        id=library.id,
        name=library.name,
        city_id=library.city_id,
        city_name=library.city.name if library.city else None,
        address=library.address,
        phone_number=library.phone_number,
    )

