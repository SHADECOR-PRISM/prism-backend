from app.db.session import supabase
from app.models.models import Project
from typing import cast, Dict, Any, List

# モデル未定義のカラムが DB に追加されても TypeError にならないよう、既知の列だけを渡す
def _to_project(row: Dict[str, Any]) -> Project:
    known = {c.key for c in Project.__table__.columns}
    return Project(**{k: v for k, v in row.items() if k in known})

def get_project(project_id: str):
    response = supabase.table("projects").select("*").eq("id", project_id).single().execute()
    return _to_project(cast(Dict[str, Any], response.data))

# is_active = True の稼働中プロジェクト一覧を取得する
def get_active_projects() -> List[Project]:
    response = supabase.table("projects").select("*").eq("is_active", True).execute()
    return [_to_project(cast(Dict[str, Any], row)) for row in response.data]
