from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import init_db
from .routes import router

app = FastAPI(title=settings.app_name, version=settings.version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"] ,
    allow_headers=["*"],
)

app.include_router(router)

@app.on_event("startup")
def on_startup():
    init_db()
