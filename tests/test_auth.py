import pytest
from sqlalchemy import update

from app.models.source import Source


@pytest.mark.asyncio
async def test_invalid_api_key_returns_401(client):
    response = await client.get(
        "/api/v1/events",
        headers={"X-API-Key": "wrong-key"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid API key"}


@pytest.mark.asyncio
async def test_inactive_source_returns_403(client, db_session):
    create_response = await client.post(
        "/api/v1/sources",
        json={
            "name": "inactive-source",
            "api_key": "inactive-key",
        },
    )

    assert create_response.status_code == 201

    await db_session.execute(
        update(Source)
        .where(Source.api_key == "inactive-key")
        .values(is_active=False)
    )
    await db_session.commit()

    response = await client.get(
        "/api/v1/events",
        headers={"X-API-Key": "inactive-key"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Source is inactive"}
