from ast import List
from fastapi import APIRouter, Depends
from sqlmodel import SQLModel, Session

from app.admin.controllers import delete_role
from app.admin.schemas import CreateAdminRequest, CreateLibrarianRequest, CreateRoleRequest, CreateRoleResponse
from app.auth.service import hash_password
from app.common.controllers import create_object, get_object_or_404, quick_select
from app.common.dependencies import AdminUserDep, RootUserDep, SessionDep
from app.models.role import Role
from app.models.user import User


admin_router = APIRouter(prefix="/admin", tags=["admin"])


@admin_router.post("/roles/", response_model=CreateRoleResponse)
async def create_role_route(role: CreateRoleRequest, session: SessionDep):
    return create_object(session, model=Role, **role.model_dump())


@admin_router.post("/create-admin/", response_model=User)
async def create_admin_route(admin: CreateAdminRequest, session: SessionDep, user: RootUserDep):
    admin_data = admin.model_dump()
    admin_data["password"] = hash_password(admin_data["password"])
    return create_object(session, model=User, **admin_data)


@admin_router.post("/create-librarian/", response_model=User)
async def create_librarian_route(librarian: CreateLibrarianRequest, session: SessionDep, user: AdminUserDep):
    librarian_data = librarian.model_dump()
    librarian_data["password"] = hash_password(librarian_data["password"])
    return create_object(session, model=User, **librarian_data)


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
        }
    )

@admin_router.delete("/delete-all-tables/")
async def delete_all_tables_route(session: SessionDep):
    SQLModel.metadata.drop_all(session.get_bind())
    return {"message": "All tables deleted and created"}

@admin_router.get("/get-all-users/")
async def get_all_users_route(session: SessionDep):
    users = (await quick_select(session=session, model=User)).scalars().all()
    users_with_role = []
    for user in users:
        users_with_role.append({
            "id": user.id,
            "name": user.name,
            "surname": user.surname,
            "email": user.email,
            "role": user.role.name,
        })
    return users_with_role

@admin_router.delete("/delete-role/{role_id}/")
async def delete_role_route(role_id: int, session: SessionDep, user: AdminUserDep):
    delete_role(session=session, role_id=role_id)
    return {"message": "Role deleted"}