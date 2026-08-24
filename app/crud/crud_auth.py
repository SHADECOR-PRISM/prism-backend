from app.db.session import supabase

#サインイン認証
def sign_in(email: str, password: str):
  response = supabase.auth.sign_in_with_password({
    "email": email,
    "password": password
  })
  
  if response is None:
    raise Exception
  
  return response

def refresh_session(refresh_token: str):
    response = supabase.auth.refresh_session(refresh_token)
    
    if response is None:
      raise Exception
    
    return response

#サインアウト
def sign_out():
  supabase.auth.sign_out()

