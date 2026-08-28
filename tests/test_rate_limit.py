import pytest


@pytest.mark.asyncio
async def test_rate_limit_returns_429_after_limit(client):
    source_response = await client.post(
        "/api/v1/sources",
        json={
            "name": "rate-limit-source",
            "api_key": "rate-limit-key",
        },
    )

    assert source_response.status_code == 201

    event_data = {
        "external_id": "rate-limit-event",
        "severity": 3,
        "event_type": "payment_failed",
        "payload": {},
        "occurred_at": "2026-08-28T10:00:00Z",
    }

    for i in range(10):
        response = await client.post(
            "/api/v1/events",
            json=event_data,
            headers={
                "X-API-Key": "rate-limit-key",
                "Idempotency-Key": f"request-{i}",
            },
        )

        assert response.status_code in (200, 201)

    response = await client.post(
        "/api/v1/events",
        json=event_data,
        headers={
            "X-API-Key": "rate-limit-key",
            "Idempotency-Key": "request-11",
        },
    )

    assert response.status_code == 429
    assert response.headers["Retry-After"] == "60"
    assert response.json() == {"detail": "Rate limit exceeded"}
