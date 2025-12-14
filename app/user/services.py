from sqlmodel import Session

from app.auth.service import verify_password
from app.auth.types import JWTTokenType
from app.common.controllers import create_object, get_object_or_404, quick_select
from app.common.dependencies import get_db_session
from app.common.exceptions import (
    InvalidUserCredentialsException,
    UserDoesNotExistException,
)
from app.models.role import Role
from app.models.user import User
from app.user.schemas import UserLoginResponse


async def create_user(
    session: get_db_session,
    email: str,
    password: str,
    role_id: int,
    name: str,
    surname: str,
) -> User | None:
    from app.auth.service import hash_password

    user = User(
        email=email,
        password=hash_password(password),
        role_id=role_id,
        name=name,
        surname=surname,
    )
    created_user = create_object(session, model=User, **user.model_dump())
    return created_user


async def login_user(session: Session, email: str, password: str) -> UserLoginResponse:
    from app.auth.service import create_jwt_token

    user = (
        await quick_select(session=session, model=User, filter_by={"email": email})
    ).scalar()
    if user is None:
        raise InvalidUserCredentialsException

    if not verify_user_password(user, password):
        raise InvalidUserCredentialsException
    role_name = await get_object_or_404(
        session=session,
        model=Role,
        id=user.role_id,
    )
    return UserLoginResponse(
        access_token=create_jwt_token(
            user_id=user.id, token_type=JWTTokenType.access, role_name=role_name.name
        ),
        refresh_token=create_jwt_token(
            user_id=user.id, token_type=JWTTokenType.refresh, role_name=role_name.name
        ),
    )


def verify_user_password(user: User, plain_password: str) -> bool:
    return verify_password(plain_password, user.password)
