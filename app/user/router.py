from fastapi import APIRouter, HTTPException, status

from app.common.controllers import get_object_or_404, quick_select
from app.common.dependencies import SessionDep, UserDep
from app.common.exceptions import InvalidJWTTokenException, InvalidUserCredentialsException
from app.models.role import Role
from app.models.user import User
from app.user.schemas import (
    RegisterRequest,
    TokenObtainByRefreshResponse,
    TokenRefreshInputSchema,
    UserLoginRequest,
    UserLoginResponse,
    UserProfileUpdate,
    UserSelfResponse,
)
from sqlmodel import select
from passlib.hash import bcrypt
from app.user.services import create_user, login_user

user_router = APIRouter(prefix="/users", tags=["users"])


@user_router.get("/self/", response_model=UserSelfResponse)
async def get_self_route(session: SessionDep, user: UserDep):
    db_user = await get_object_or_404(session=session, model=User, id=user["user_id"])

    return UserSelfResponse(
        name=db_user.name,
        email=db_user.email,
        surname=db_user.surname,
        phone_number=db_user.phone_number,
        user_id=db_user.id,
        role_name=user["role_name"],
    )


@user_router.put("/self/", response_model=UserSelfResponse)
async def update_self_route(data: UserProfileUpdate, session: SessionDep, user: UserDep):
    db_user = await get_object_or_404(session=session, model=User, id=user["user_id"])

    if data.email is not None:
        existing = session.exec(select(User).where(User.email == data.email)).first()
        if existing and existing.id != db_user.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Email already in use"
            )
        db_user.email = data.email
    if data.name is not None:
        db_user.name = data.name
    if data.surname is not None:
        db_user.surname = data.surname
    if data.phone_number is not None:
        db_user.phone_number = data.phone_number
    if data.password is not None:
        db_user.password = bcrypt.hash(data.password)

    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return UserSelfResponse(
        name=db_user.name,
        email=db_user.email,
        surname=db_user.surname,
        phone_number=db_user.phone_number,
        user_id=db_user.id,
        role_name=user["role_name"],
    )


@user_router.post("/register/", response_model=UserLoginResponse)
async def register_user_route(registration_data: RegisterRequest, session: SessionDep):
    role = (await quick_select(session=session, model=Role, filter_by={"name": "reader"})).scalar()
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Default role 'reader' not found. Seed roles first.",
        )
    await create_user(
        session,
        email=registration_data.email,
        password=registration_data.password,
        role_id=role.id,
        name=registration_data.name,
        surname=registration_data.surname,
    )
    return await login_user(
        session, email=registration_data.email, password=registration_data.password
    )


@user_router.post("/login/", response_model=UserLoginResponse)
async def login_user_route(credentials: UserLoginRequest, session: SessionDep):
    try:
        return await login_user(
            session, email=credentials.email, password=credentials.password
        )
    except InvalidUserCredentialsException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )


@user_router.post("/tokens/obtain/", response_model=TokenObtainByRefreshResponse)
async def obtain_access_token_route(token_info: TokenRefreshInputSchema):
    from app.auth.service import issue_access_token_by_refresh_token

    try:
        return TokenObtainByRefreshResponse(
            access_token=issue_access_token_by_refresh_token(token_info.refresh_token)
        )
    except InvalidJWTTokenException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
