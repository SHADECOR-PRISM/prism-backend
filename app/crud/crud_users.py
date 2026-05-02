from app.db.session import supabase

def get_user(token : str):
  response = supabase.auth.get_user(token)
  return response
