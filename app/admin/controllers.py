from fastapi import HTTPException
from starlette import status

from app.admin.schemas import EditUserRequest
from app.common.controllers import get_object_or_404, quick_select
from app.common.dependencies import SessionDep
from app.models.role import Role
from app.models.user import User


async def check_email_available(session: SessionDep, email: str, exclude_user_id: int | None = None):
    existing_user = (await quick_select(
        session=session,
        model=User,
        filters=[User.email == email]
    )).scalar()
    
    if existing_user and existing_user.id != exclude_user_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already in use"
        )


async def delete_role(session: SessionDep, role_id: int):
    role = await get_object_or_404(session, Role, id=role_id)
    session.delete(role)
    session.commit()


async def delete_user(session: SessionDep, user_id: int):
    user = await get_object_or_404(session, User, id=user_id)
    session.delete(user)
    session.commit()


async def edit_user(session: SessionDep, user_id: int, new_user: EditUserRequest, hashed_password: str | None = None):
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
