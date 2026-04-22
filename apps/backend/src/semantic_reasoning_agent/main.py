from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from semantic_reasoning_agent.entrypoints.router import api_router
from semantic_reasoning_agent.core.config import get_settings
from semantic_reasoning_agent.persistence.database import get_database_manager
from semantic_reasoning_agent.services.alembic_service import AlembicService


@asynccontextmanager
async def lifespan(_: FastAPI):
    database_manager = get_database_manager()
    AlembicService(database_manager).upgrade()
    yield


settings = get_settings()
app = FastAPI(title=settings.app_name, lifespan=lifespan)
allowed_origins = [origin.strip() for origin in settings.cors_allow_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health", tags=["system"])
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
