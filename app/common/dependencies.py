from typing import Annotated
from fastapi import Depends, HTTPException, Header, status
from sqlmodel import Session
from fastapi.security import OAuth2PasswordBearer

from app.auth.service import decode_jwt_token
from app.common.exceptions import InvalidJWTTokenException
from database import engine

oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")


async def get_db_session() -> Session:
    with Session(engine) as session:
        yield session


async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = decode_jwt_token(token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate user",
            )
        user_id: int = int(payload.user_id)
        role_name: str = payload.role_name
        if not role_name or not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate user",
            )
        return {"user_id": user_id, "role_name": role_name}
    except InvalidJWTTokenException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


UserDep = Annotated[dict, Depends(get_current_user)]


def require_librarian(user: UserDep):
    role = str(user.get("role_name", "")).lower()
    if role != "librarian":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to access this resource",
        )
    return user


def require_root(user: UserDep):
    role = str(user.get("role_name", "")).lower()
    if role != "root":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to access this resource",
        )
    return user


def require_librarian_or_root(user: UserDep):
    role = str(user.get("role_name", "")).lower()
    if role not in ("librarian", "root"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to access this resource",
        )
    return user


LibrarianUserDep = Annotated[dict, Depends(require_librarian)]
RootUserDep = Annotated[dict, Depends(require_root)]
LibrarianOrRootUserDep = Annotated[dict, Depends(require_librarian_or_root)]
SessionDep = Annotated[Session, Depends(get_db_session)]
