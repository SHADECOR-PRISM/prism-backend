from typing import List
from fastapi import APIRouter, Depends
from app.api.deps import get_current_user
from app.models.models import Users
from app.schemas.project import ProjectRead
from app.crud.crud_projects import get_active_projects

router = APIRouter(prefix="/projects", tags=["projects"])

# 申請フォームの選択肢として使用する稼働中のプロジェクト一覧を取得
@router.get("", response_model=List[ProjectRead], operation_id="readProjects")
async def read_projects(current_user: Users = Depends(get_current_user)):
    projects = get_active_projects()
    return projects