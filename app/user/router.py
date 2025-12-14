from fastapi import APIRouter, HTTPException, status

from app.common.controllers import get_object_or_404, quick_select
from app.common.dependencies import SessionDep, UserDep
from app.common.exceptions import (
    InvalidJWTTokenException,
    InvalidUserCredentialsException,
)
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
from app.readers.schemas import CreateReaderRequest
from app.readers.controllers import create_reader
from app.models.reader_category import ReaderCategory
from app.models.reader import Reader
from app.models.rent import Rent
from app.models.penalty import Penalty
from sqlmodel import select
from sqlalchemy import func
from passlib.hash import bcrypt
from app.user.services import create_user, login_user
from app.event_log.decorators import audit_log
from app.user.schemas import ReaderInfoResponse
from app.user.notifications_controller import (
    get_user_notifications,
    get_unread_count,
    mark_as_read,
    mark_all_as_read,
)
from fastapi import Request

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
@audit_log(
    action_type="update",
    entity_type="user",
    get_entity_id=lambda result, user, *args, **kwargs: user["user_id"],
    get_description=lambda result, user, *args, **kwargs: (
        f"Користувач оновив свій профіль"
    ),
    get_old_values=lambda result, session, user, *args, **kwargs: (
        {
            "email": db_user.email,
            "name": db_user.name,
            "surname": db_user.surname,
        }
        if session and (db_user := session.get(User, user["user_id"]))
        else None
    ),
    get_new_values=lambda result, *args, **kwargs: (
        {
            "email": result.email,
            "name": result.name,
            "surname": result.surname,
        }
        if result
        else None
    ),
)
async def update_self_route(
    data: UserProfileUpdate, session: SessionDep, user: UserDep
):
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
@audit_log(
    action_type="create",
    entity_type="user",
    get_entity_id=lambda result, session, registration_data, *args, **kwargs: (
        created.id
        if session
        and (
            created := session.exec(
                select(User).where(User.email == registration_data.email)
            ).first()
        )
        else None
    ),
    get_description=lambda result, registration_data, *args, **kwargs: (
        f"Зареєстровано нового користувача '{registration_data.email}'"
    ),
    get_new_values=lambda result, registration_data, *args, **kwargs: {
        "email": registration_data.email,
        "name": registration_data.name,
        "surname": registration_data.surname,
        "role": "reader",
    },
)
async def register_user_route(
    registration_data: RegisterRequest, session: SessionDep, request: Request
):
    role = (
        await quick_select(session=session, model=Role, filter_by={"name": "reader"})
    ).scalar()
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Default role 'reader' not found. Seed roles first.",
        )
    created_user = await create_user(
        session,
        email=registration_data.email,
        password=registration_data.password,
        role_id=role.id,
        name=registration_data.name,
        surname=registration_data.surname,
    )
    default_category = session.exec(select(ReaderCategory)).first()
    if default_category is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Default reader category not found. Seed reader categories first.",
        )
    create_reader(
        session,
        CreateReaderRequest(
            name=registration_data.name,
            surname=registration_data.surname,
            phone_number=None,
            address=None,
            reader_category_id=default_category.id,
            user_id=created_user.id,
        ),
    )
    result = await login_user(
        session, email=registration_data.email, password=registration_data.password
    )
    return result


@user_router.post("/login/", response_model=UserLoginResponse)
@audit_log(
    action_type="login",
    entity_type="user",
    get_entity_id=lambda result, session, credentials, *args, **kwargs: (
        user.id
        if session
        and (
            user := session.exec(
                select(User).where(User.email == credentials.email)
            ).first()
        )
        else None
    ),
    get_description=lambda result, credentials, *args, **kwargs: (
        f"Користувач {credentials.email} увійшов у систему"
    ),
    get_additional_metadata=lambda result, credentials, *args, **kwargs: {
        "email": credentials.email,
    },
)
async def login_user_route(
    credentials: UserLoginRequest, session: SessionDep, request: Request
):
    try:
        result = await login_user(
            session, email=credentials.email, password=credentials.password
        )
        return result
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


@user_router.get("/self/reader-info/", response_model=ReaderInfoResponse)
async def get_reader_info_route(session: SessionDep, user: UserDep):
    reader = session.exec(
        select(Reader).where(Reader.user_id == user["user_id"])
    ).first()

    if not reader:
        return ReaderInfoResponse(reader_category_name=None, total_debt=0.0)

    reader_category_name = None
    if reader.reader_category_id:
        category = session.get(ReaderCategory, reader.reader_category_id)
        if category:
            reader_category_name = category.name

    from app.rents.utils import calculate_total_debt_for_rents

    all_rents = session.exec(select(Rent).where(Rent.reader_id == reader.id)).all()

    total_debt = calculate_total_debt_for_rents(session, all_rents)

    return ReaderInfoResponse(
        reader_category_name=reader_category_name, total_debt=total_debt
    )


@user_router.get("/self/notifications/")
async def get_notifications_route(session: SessionDep, user: UserDep):
    notifications = get_user_notifications(session, user["user_id"])
    return [
        {
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat(),
            "book_id": n.book_id,
        }
        for n in notifications
    ]


@user_router.get("/self/notifications/unread-count/")
async def get_unread_count_route(session: SessionDep, user: UserDep):
    count = get_unread_count(session, user["user_id"])
    return {"count": count}


@user_router.post("/self/notifications/{notification_id}/read/")
async def mark_notification_read_route(
    notification_id: int, session: SessionDep, user: UserDep
):
    if not mark_as_read(session, notification_id, user["user_id"]):
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Notification marked as read"}


@user_router.post("/self/notifications/read-all/")
async def mark_all_notifications_read_route(session: SessionDep, user: UserDep):
    mark_all_as_read(session, user["user_id"])
    return {"message": "All notifications marked as read"}
