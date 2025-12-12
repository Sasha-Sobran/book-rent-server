from ast import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import SQLModel, Session

from app.admin.controllers import add_user, check_email_available, delete_role, delete_user, edit_user
from app.admin.schemas import (
    CreateAdminRequest,
    CreateLibrarianRequest,
    CreateRoleRequest,
    CreateRoleResponse,
    EditUserRequest,
)
from app.auth.service import hash_password
from app.common.controllers import create_object, get_object_or_404, quick_select
from app.common.dependencies import AdminUserDep, RootUserDep, SessionDep
from app.admin.controllers import create_librarian
from app.models.role import Role
from app.models.user import User


admin_router = APIRouter(prefix="/admin", tags=["admin"])


@admin_router.post("/roles/", response_model=CreateRoleResponse)
async def create_role_route(role: CreateRoleRequest, session: SessionDep):
    return create_object(session, model=Role, **role.model_dump())


@admin_router.post("/create-root/")
async def create_root_route(session: SessionDep):
    return create_object(
        session,
        model=User,
        **{
            "email": "root@example.com",
            "password": hash_password("root"),
            "role_id": 1,
            "surname": "root",
            "name": "root",
            "phone_number": "1234567890",
        },
    )


@admin_router.delete("/delete-all-tables/")
async def delete_all_tables_route(session: SessionDep):
    SQLModel.metadata.drop_all(session.get_bind())
    return {"message": "All tables deleted and created"}


@admin_router.get("/get-users/")
async def get_users_route(
    session: SessionDep,
    role_id: int | None = None,
    query: str | None = None,
):
    from sqlalchemy import or_
    
    filters = []
    
    if role_id is not None:
        filters.append(User.role_id == role_id)
    
    if query:
        filters.append(
            or_(
                User.name.ilike(f"%{query}%"),
                User.surname.ilike(f"%{query}%"),
                User.email.ilike(f"%{query}%"),
            )
        )
    
    users = (await quick_select(session=session, model=User, filters=filters)).scalars().all()
    
    users_with_role = []
    for user in users:
        users_with_role.append(
            {
                "id": user.id,
                "name": user.name,
                "surname": user.surname,
                "email": user.email,
                "role": user.role.name,
                "phone_number": user.phone_number,
            }
        )
    return users_with_role


@admin_router.delete("/delete-role/{role_id}/")
async def delete_role_route(role_id: int, session: SessionDep, user: AdminUserDep):
    await delete_role(session=session, role_id=role_id)
    return {"message": "Role deleted"}


@admin_router.put("/edit-user/{user_id}/")
async def edit_user_route(
    user_id: int, new_user: EditUserRequest, session: SessionDep, user: AdminUserDep
):
    await check_email_available(session=session, email=new_user.email, exclude_user_id=user_id)
    hashed_password = hash_password(new_user.password) if new_user.password else None
    await edit_user(session=session, user_id=user_id, new_user=new_user, hashed_password=hashed_password)
    return {"message": "User edited"}


@admin_router.post("/create-user/")
async def add_user_route(new_user: User, session: SessionDep, user: AdminUserDep):
    await check_email_available(session=session, email=new_user.email)
    new_user.password = hash_password(new_user.password)
    await add_user(session=session, new_user=new_user)
    return {"message": "User added"}


@admin_router.post("/create-librarian/")
async def create_librarian_route(payload: CreateLibrarianRequest, session: SessionDep, user: AdminUserDep):
    await check_email_available(session=session, email=payload.email)
    role = (await quick_select(session=session, model=Role, filter_by={"name": "librarian"})).scalar_one_or_none()
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role 'librarian' not found. Seed roles first.",
        )
    hashed_password = hash_password(payload.password)
    await create_librarian(session=session, data=payload, hashed_password=hashed_password, role_id=role.id)
    return {"message": "Librarian created"}

@admin_router.delete("/delete-user/{user_id}/")
async def delete_user_route(user_id: int, session: SessionDep, user: AdminUserDep):
    await delete_user(session=session, user_id=user_id)
    return {"message": "User deleted"}