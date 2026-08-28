from uuid import uuid4

import pytest


@pytest.mark.asyncio
async def test_create_source(client):
    source_name = f"test-source-{uuid4()}"

    response = await client.post(
        "/api/v1/sources",
        json={
            "name": source_name,
            "api_key": "test-api-key",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == source_name
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_get_sources(client):
    source_name = f"test-source-{uuid4()}"

    create_response = await client.post(
        "/api/v1/sources",
        json={
            "name": source_name,
            "api_key": "test-api-key",
        },
    )

    assert create_response.status_code == 201

    response = await client.get("/api/v1/sources")

    assert response.status_code == 200

    sources = response.json()

    assert len(sources) == 1
    assert sources[0]["name"] == source_name
