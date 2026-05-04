from dotenv import load_dotenv
load_dotenv()

import os

#supabase
SUPABASE_URL = str(os.getenv('SUPABASE_URL'))
SUPABASE_KEY = str(os.getenv('SUPABASE_KEY'))
ADD_EMAIL_ADRESS = str(os.getenv('ADD_EMAIL_ADRESS'))

# local development
FRONTEND_URL="http://localhost:3000"
