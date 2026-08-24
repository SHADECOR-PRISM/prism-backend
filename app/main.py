# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth
from app.api import user
from app.api import projects
from app.api.accounting import requests
from app.core.config import FRONTEND_URL
from app.core.exceptions import global_exception_handler 

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

# ★ 例外ハンドラーの登録
app.add_exception_handler(Exception, global_exception_handler)

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(projects.router)
app.include_router(requests.router)