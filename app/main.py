from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth
from app.core.config import FRONTEND_URL

app = FastAPI()

app.add_middleware(
  CORSMiddleware,
  allow_origins = [
    FRONTEND_URL,
  ],
  allow_credentials = True,
  allow_methods = ["*"],
  allow_headers = ["*"],
)

app.include_router(auth.router)
