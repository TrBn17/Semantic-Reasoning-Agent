from contextlib import asynccontextmanager

from fastapi import FastAPI

from semantic_reasoning_agent.api.router import api_router
from semantic_reasoning_agent.config import get_settings
from semantic_reasoning_agent.db.database import get_database_manager


@asynccontextmanager
async def lifespan(_: FastAPI):
    get_database_manager().create_schema()
    yield


settings = get_settings()
app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health", tags=["system"])
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}