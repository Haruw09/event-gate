from fastapi import FastAPI
from sqlalchemy import text

from app.api.sources import router as sources_router
from app.db import engine
from app.redis_client import redis_client

app = FastAPI()

app.include_router(sources_router)


@app.get("/health")
async def health() -> dict[str, str]:
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))

    await redis_client.ping()

    return {"status": "ok"}
