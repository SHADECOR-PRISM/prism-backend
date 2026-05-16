from app.db.session import supabase
from app.models.models import Project
from typing import cast, Dict, Any

def get_project(project_id: str):

  response = supabase.table("projects").select("*").eq("id", project_id).single().execute()
  
  return Project(**cast(Dict[str, Any], response.data))
  
