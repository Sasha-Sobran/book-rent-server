from datetime import UTC, datetime, timedelta
from app.common.controllers import get_object_or_404
from uuid import UUID

from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.types import JWTTokenPayload, JWTTokenType
from app.common.exceptions import InvalidJWTTokenException, UserNotFoundException
from app.common.settings import Settings
from app.models.user import User

settings = Settings()

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_jwt_token(user_id: UUID, token_type: JWTTokenType, role_name: str) -> str:
    token_type_to_expiration_delta = {
        JWTTokenType.access: timedelta(
            minutes=settings.access_token_expiration_time_in_minutes
        ),
        JWTTokenType.refresh: timedelta(
            days=settings.refresh_token_expiration_time_in_days
        ),
    }
    expiration_datetime = datetime.now(UTC) + token_type_to_expiration_delta[token_type]
    token_data = {
        "user_id": str(user_id),
        "token_type": token_type.name,
        "exp": expiration_datetime,
        "role_name": role_name,
    }
    encoded_jwt = jwt.encode(
        token_data,
        settings.encoding_key,
        algorithm=settings.encoding_algorithm,
        headers={"typ": "JWT", "alg": settings.encoding_algorithm},
    )
    return encoded_jwt


def decode_jwt_token(token: str) -> JWTTokenPayload | None:
    try:
        payload = jwt.decode(
            token, settings.encoding_key, algorithms=[settings.encoding_algorithm]
        )
        expiration_datetime = datetime.fromtimestamp(float(payload.pop("exp", 0)), tz=UTC)
        return JWTTokenPayload(**payload, exp=expiration_datetime) if payload else None
    except ExpiredSignatureError:
        raise InvalidJWTTokenException
    except JWTError:
        raise InvalidJWTTokenException


async def validate_jwt_token_payload(
    session: AsyncSession, payload: JWTTokenPayload, token_type: JWTTokenType
) -> User:
    if payload.token_type != token_type.name or payload.exp < datetime.now(UTC):
        raise InvalidJWTTokenException
    user = await get_object_or_404(
        session=session, model=User, filters=[User.id == payload.user_id]
    )
    if user is None:
        raise UserNotFoundException
    return user


def issue_access_token_by_refresh_token(refresh_token: str) -> str:
    payload = decode_jwt_token(refresh_token)
    if payload is None or payload.exp < datetime.now(UTC):
        raise InvalidJWTTokenException
    try:
        user_id = UUID(payload.user_id)
    except (ValueError, TypeError):
        raise InvalidJWTTokenException
    return create_jwt_token(
        user_id=user_id,
        token_type=JWTTokenType.access,
        role_name=payload.role_name,
    )


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    print(plain_password, hashed_password)
    print(password_context.hash(plain_password))
    print(password_context.verify(plain_password, hashed_password))
    return password_context.verify(plain_password, hashed_password)
