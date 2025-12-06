from fastapi import APIRouter, HTTPException, status

from app.common.controllers import get_object_or_404
from app.common.dependencies import SessionDep, UserDep
from app.common.exceptions import InvalidJWTTokenException
from app.models.role import Role
from app.models.user import User
from app.user.schemas import (
    RegisterRequest,
    TokenObtainByRefreshResponse,
    TokenRefreshInputSchema,
    UserLoginRequest,
    UserLoginResponse,
    UserSelfResponse,
)
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


@user_router.post("/register/", response_model=UserLoginResponse)
async def register_user_route(registration_data: RegisterRequest, session: SessionDep):
    await create_user(
        session,
        email=registration_data.email,
        password=registration_data.password,
        role_id=(
            await get_object_or_404(session=session, model=Role, name="reader")
        ).id,
        name=registration_data.name,
    )
    return await login_user(
        session, email=registration_data.email, password=registration_data.password
    )


@user_router.post("/login/", response_model=UserLoginResponse)
async def login_user_route(credentials: UserLoginRequest, session: SessionDep):
    return await login_user(
        session, email=credentials.email, password=credentials.password
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
