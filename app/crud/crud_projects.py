from app.db.session import supabase
from app.models.models import Project
from typing import cast, Dict, Any, List

def get_project(project_id: str):
    response = supabase.table("projects").select("*").eq("id", project_id).single().execute()
    return Project(**cast(Dict[str, Any], response.data))

# is_active = True の稼働中プロジェクト一覧を取得する
def get_active_projects() -> List[Project]:
    response = supabase.table("projects").select("*").eq("is_active", True).execute()
    return [Project(**cast(Dict[str, Any], row)) for row in response.data]