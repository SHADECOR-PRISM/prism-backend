from fastapi import APIRouter, Depends
from datetime import datetime
from app.api.deps import get_current_user
from app.crud.crud_container import get_user_container
from app.crud.crud_projects import get_project
from app.schemas.accounting import Container
from app.models.models import Users

router = APIRouter()

@router.get("/container/me", response_model = list[Container])
async def get_container_me(start: datetime, end: datetime, offset: int, current_user: Users = Depends(get_current_user)):
    containers = get_user_container(current_user.id, start, end, offset)

    return [{
        "id": container.id,
        "user_id": current_user.user_id,
        "project_name": get_project(container.project_id).name,
        "category": container.category,
        "applied_at": datetime.fromisoformat(container.applied_at).strftime("%Y/%m/%d"),
        "status": container.status,
        "total_amount": container.total_amount
    } for container in containers]