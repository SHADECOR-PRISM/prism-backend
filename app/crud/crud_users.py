from app.db.session import supabase
from app.models.models import Users
from typing import cast, Dict, Any

def get_user(token : str):
  auth_response = supabase.auth.get_user(token)
  if not auth_response:
    return None
  
  users_response = supabase.table("users").select("*").eq("id", auth_response.user.id).single().execute()

  if not users_response:
      return None
  
  return Users(**cast(Dict[str, Any], users_response.data))
  
