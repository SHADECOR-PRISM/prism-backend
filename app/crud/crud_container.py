from datetime import datetime
from app.db.session import supabase
from app.models.models import ApplicationHeader
from typing import cast, Dict, Any
import app.core.config as config

def get_user_container(user_id: str, start: datetime, end: datetime, offset: int):

  response = (
    supabase.table("application_header").select("*")
    .eq("user_id", user_id).gte("applied_at", start.isoformat()).lt("applied_at", end.isoformat())
    .order("applied_at", desc=True).range(offset, offset + config.FETCH_LIMIT - 1).execute()
  )
  
  return [ApplicationHeader(**cast(Dict[str, Any], item)) for item in response.data]
