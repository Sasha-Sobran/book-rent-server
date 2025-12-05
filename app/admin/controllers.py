from app.common.controllers import get_object_or_404
from app.common.dependencies import SessionDep
from app.models.role import Role

def delete_role(session: SessionDep, role_id: int) -> Role:
    role = get_object_or_404(session, Role, id=role_id)
    session.delete(role)
    session.commit()
    return role