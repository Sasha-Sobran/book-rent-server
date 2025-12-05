from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.common.controllers import quick_select
from app.common.dependencies import SessionDep
from app.models.role import Role


common_router = APIRouter(prefix="", tags=["common"])


@common_router.get("/health/")
async def health_route():
    return {"status": "ok"}


@common_router.get("/roles/")
async def get_roles_route(session: SessionDep):
    result = await quick_select(session=session, model=Role)
    return result.scalars().all()
