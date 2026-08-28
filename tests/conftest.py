import os

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

os.environ["DATABASE_URL"] = (
    "postgresql+asyncpg://postgres:postgres@localhost:5433/event_gate_test"
)
os.environ["REDIS_URL"] = "redis://localhost:6380/0"


from app.db import engine
from app.main import app
from app.models.alert import Alert
from app.models.event import Event
from app.models.rule import Rule
from app.models.source import Source
from app.redis_client import redis_client


@pytest_asyncio.fixture(autouse=True)
async def clean_test_state():
    async with engine.begin() as connection:
        await connection.execute(delete(Alert))
        await connection.execute(delete(Event))
        await connection.execute(delete(Rule))
        await connection.execute(delete(Source))

    await redis_client.flushdb()

    yield


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        yield client


@pytest_asyncio.fixture
async def db_session():
    from app.db import SessionLocal

    async with SessionLocal() as session:
        yield session
