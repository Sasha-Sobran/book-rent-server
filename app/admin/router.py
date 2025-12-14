from ast import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import SQLModel, Session, select

from app.admin.controllers import (
    add_user,
    check_email_available,
    delete_role,
    delete_user,
    edit_user,
    validate_assignable_role,
)
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
from app.event_log.decorators import audit_log


admin_router = APIRouter(prefix="/admin", tags=["admin"])


@admin_router.post("/roles/", response_model=CreateRoleResponse)
@audit_log(
    action_type="create",
    entity_type="role",
    get_entity_id=lambda result, *args, **kwargs: result.id if result else None,
    get_description=lambda result, *args, **kwargs: (
        f"Створено роль '{result.name}'" if result else None
    ),
    get_new_values=lambda result, *args, **kwargs: (
        {
            "name": result.name,
        }
        if result
        else None
    ),
)
async def create_role_route(
    role: CreateRoleRequest, session: SessionDep, user: AdminUserDep
):
    return create_object(session, model=Role, **role.model_dump())


@admin_router.post("/create-root/")
async def create_root_route(session: SessionDep):
    root_role = (
        (await quick_select(session=session, model=Role, filter_by={"name": "root"}))
        .scalars()
        .first()
    )
    if root_role is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role 'root' not found. Seed roles first.",
        )
    existing_root = (
        (
            await quick_select(
                session=session, model=User, filters=[User.role_id == root_role.id]
            )
        )
        .scalars()
        .first()
    )
    if existing_root:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Root user already exists",
        )
    return create_object(
        session,
        model=User,
        **{
            "email": "root@example.com",
            "password": hash_password("root"),
            "role_id": root_role.id,
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

    users = (
        (await quick_select(session=session, model=User, filters=filters))
        .scalars()
        .all()
    )

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
@audit_log(
    action_type="delete",
    entity_type="role",
    get_entity_id=lambda result, role_id, *args, **kwargs: role_id,
    get_description=lambda result, session, role_id, *args, **kwargs: (
        f"Видалено роль '{role.name}'"
        if session and (role := session.get(Role, role_id))
        else f"Видалено роль (ID: {role_id})"
    ),
    get_old_values=lambda result, session, role_id, *args, **kwargs: (
        {
            "name": role.name,
        }
        if session and (role := session.get(Role, role_id))
        else None
    ),
)
async def delete_role_route(role_id: int, session: SessionDep, user: AdminUserDep):
    await delete_role(session=session, role_id=role_id)
    return {"message": "Role deleted"}


@admin_router.put("/edit-user/{user_id}/")
@audit_log(
    action_type="update",
    entity_type="user",
    get_entity_id=lambda result, user_id, *args, **kwargs: user_id,
    get_description=lambda result, session, user_id, new_user, *args, **kwargs: (
        f"Оновлено користувача '{old_user.email}'"
        if session and (old_user := session.get(User, user_id))
        else f"Оновлено користувача (ID: {user_id})"
    ),
    get_old_values=lambda result, session, user_id, *args, **kwargs: (
        {
            "email": old_user.email,
            "name": old_user.name,
            "surname": old_user.surname,
            "role_id": old_user.role_id,
        }
        if session and (old_user := session.get(User, user_id))
        else None
    ),
    get_new_values=lambda result, new_user, *args, **kwargs: (
        {
            "email": new_user.email,
            "name": new_user.name,
            "surname": new_user.surname,
            "role_id": new_user.role_id,
        }
        if "new_user" in kwargs
        else None
    ),
)
async def edit_user_route(
    user_id: int, new_user: EditUserRequest, session: SessionDep, user: AdminUserDep
):
    await check_email_available(
        session=session, email=new_user.email, exclude_user_id=user_id
    )
    await validate_assignable_role(session, user["role_name"], new_user.role_id)
    hashed_password = hash_password(new_user.password) if new_user.password else None
    await edit_user(
        session=session,
        user_id=user_id,
        new_user=new_user,
        hashed_password=hashed_password,
    )
    return {"message": "User edited"}


@admin_router.post("/create-user/")
@audit_log(
    action_type="create",
    entity_type="user",
    get_entity_id=lambda result, session, new_user, *args, **kwargs: (
        created.id
        if session
        and (
            created := session.exec(
                select(User).where(User.email == new_user.email)
            ).first()
        )
        else None
    ),
    get_description=lambda result, new_user, *args, **kwargs: (
        f"Створено користувача '{new_user.email}'"
    ),
    get_new_values=lambda result, new_user, *args, **kwargs: {
        "email": new_user.email,
        "name": new_user.name,
        "surname": new_user.surname,
        "role_id": new_user.role_id,
    },
)
async def add_user_route(new_user: User, session: SessionDep, user: AdminUserDep):
    await check_email_available(session=session, email=new_user.email)
    await validate_assignable_role(session, user["role_name"], new_user.role_id)
    new_user.password = hash_password(new_user.password)
    await add_user(session=session, new_user=new_user)
    return {"message": "User added"}


@admin_router.post("/create-librarian/")
@audit_log(
    action_type="create",
    entity_type="user",
    get_entity_id=lambda result, session, payload, *args, **kwargs: (
        created.id
        if session
        and (
            created := session.exec(
                select(User).where(User.email == payload.email)
            ).first()
        )
        else None
    ),
    get_description=lambda result, payload, *args, **kwargs: (
        f"Створено бібліотекаря '{payload.email}'"
    ),
    get_new_values=lambda result, payload, *args, **kwargs: {
        "email": payload.email,
        "name": payload.name,
        "surname": payload.surname,
        "library_id": payload.library_id,
        "role": "librarian",
    },
)
async def create_librarian_route(
    payload: CreateLibrarianRequest, session: SessionDep, user: AdminUserDep
):
    await check_email_available(session=session, email=payload.email)
    role = (
        (
            await quick_select(
                session=session, model=Role, filter_by={"name": "librarian"}
            )
        )
        .scalars()
        .first()
    )
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role 'librarian' not found. Seed roles first.",
        )
    hashed_password = hash_password(payload.password)
    await validate_assignable_role(session, user["role_name"], role.id)
    await create_librarian(
        session=session, data=payload, hashed_password=hashed_password, role_id=role.id
    )
    return {"message": "Librarian created"}


@admin_router.delete("/delete-user/{user_id}/")
@audit_log(
    action_type="delete",
    entity_type="user",
    get_entity_id=lambda result, user_id, *args, **kwargs: user_id,
    get_description=lambda result, session, user_id, *args, **kwargs: (
        f"Видалено користувача '{old_user.email}'"
        if session and (old_user := session.get(User, user_id))
        else f"Видалено користувача (ID: {user_id})"
    ),
    get_old_values=lambda result, session, user_id, *args, **kwargs: (
        {
            "email": old_user.email,
            "name": old_user.name,
            "surname": old_user.surname,
            "role": old_user.role.name if old_user.role else None,
        }
        if session and (old_user := session.get(User, user_id))
        else None
    ),
)
async def delete_user_route(user_id: int, session: SessionDep, user: AdminUserDep):
    await delete_user(session=session, user_id=user_id)
    return {"message": "User deleted"}
