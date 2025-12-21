from fastapi import HTTPException
from starlette import status

from app.admin.schemas import EditUserRequest
from app.admin.schemas import CreateLibrarianRequest
from app.common.controllers import create_object, get_object_or_404, quick_select
from app.common.dependencies import SessionDep
from app.models.role import Role
from app.models.librarian import Librarian
from app.models.user import User

ALLOWED_ROLE_ASSIGNMENTS = {
    "root": {"librarian"},
}


async def validate_assignable_role(
    session: SessionDep, acting_role_name: str, target_role_id: int
):
    target_role = await get_object_or_404(session, Role, id=target_role_id)
    allowed_roles = ALLOWED_ROLE_ASSIGNMENTS.get(acting_role_name.lower(), set())
    if target_role.name.lower() not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to assign this role",
        )
    return target_role


async def check_email_available(
    session: SessionDep, email: str, exclude_user_id: int | None = None
):
    existing_user = (
        await quick_select(session=session, model=User, filters=[User.email == email])
    ).scalar()

    if existing_user and existing_user.id != exclude_user_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already in use"
        )


async def delete_role(session: SessionDep, role_id: int):
    from sqlmodel import select
    from app.models.user import User
    from fastapi import HTTPException

    role = await get_object_or_404(session, Role, id=role_id)

    users_with_role = session.exec(select(User).where(User.role_id == role_id)).first()
    if users_with_role:
        raise HTTPException(
            status_code=400, detail="Cannot delete role with assigned users"
        )

    session.delete(role)
    session.commit()


async def delete_user(session: SessionDep, user_id: int):
    from sqlmodel import select, delete
    from app.models.librarian import Librarian
    from app.models.reader import Reader
    from app.models.book_notification import BookNotification

    user = await get_object_or_404(session, User, id=user_id)

    session.exec(delete(Librarian).where(Librarian.user_id == user_id))
    session.exec(delete(Reader).where(Reader.user_id == user_id))
    session.exec(delete(BookNotification).where(BookNotification.user_id == user_id))

    session.delete(user)
    session.commit()


async def edit_user(
    session: SessionDep,
    user_id: int,
    new_user: EditUserRequest,
    hashed_password: str | None = None,
):
    user = await get_object_or_404(session, User, id=user_id)
    user.name = new_user.name
    user.surname = new_user.surname
    user.email = new_user.email
    user.phone_number = new_user.phone_number
    user.role_id = new_user.role_id
    if hashed_password:
        user.password = hashed_password
    session.add(user)
    session.commit()


async def add_user(session: SessionDep, new_user: User):
    session.add(new_user)
    session.commit()


async def create_librarian(
    session: SessionDep,
    data: CreateLibrarianRequest,
    hashed_password: str,
    role_id: int,
):
    user = User(
        email=data.email,
        password=hashed_password,
        role_id=role_id,
        name=data.name,
        surname=data.surname,
        phone_number=data.phone_number,
    )
    create_object(session, model=User, **user.model_dump())
    created = (
        await quick_select(session=session, model=User, filter_by={"email": data.email})
    ).scalar_one()
    lib = Librarian(user_id=created.id, library_id=data.library_id)
    create_object(session, model=Librarian, **lib.model_dump())
