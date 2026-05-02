from supabase import create_client, Client
import app.core.config as config

supabase:Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)