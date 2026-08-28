from datetime import UTC, datetime

import pytest


@pytest.mark.asyncio
async def test_event_ingest_is_idempotent(client):
    source_response = await client.post(
        "/api/v1/sources",
        json={
            "name": "event-source",
            "api_key": "event-key",
        },
    )

    assert source_response.status_code == 201

    event_data = {
        "external_id": "evt-1",
        "severity": 4,
        "event_type": "payment_failed",
        "payload": {"order_id": "123"},
        "occurred_at": "2026-08-28T10:00:00Z",
    }

    headers = {
        "X-API-Key": "event-key",
        "Idempotency-Key": "request-1",
    }

    first_response = await client.post(
        "/api/v1/events",
        json=event_data,
        headers=headers,
    )

    assert first_response.status_code == 201

    second_response = await client.post(
        "/api/v1/events",
        json=event_data,
        headers=headers,
    )

    assert second_response.status_code == 200

    first_event = first_response.json()
    second_event = second_response.json()

    assert first_event["id"] == second_event["id"]
    assert first_event["external_id"] == second_event["external_id"]


@pytest.mark.asyncio
async def test_duplicate_external_id_returns_existing_event(client):
    source_response = await client.post(
        "/api/v1/sources",
        json={
            "name": "event-source",
            "api_key": "event-key",
        },
    )

    assert source_response.status_code == 201

    event_data = {
        "external_id": "evt-1",
        "severity": 4,
        "event_type": "payment_failed",
        "payload": {"order_id": "123"},
        "occurred_at": "2026-08-28T10:00:00Z",
    }

    first_response = await client.post(
        "/api/v1/events",
        json=event_data,
        headers={
            "X-API-Key": "event-key",
            "Idempotency-Key": "request-1",
        },
    )

    assert first_response.status_code == 201

    second_response = await client.post(
        "/api/v1/events",
        json=event_data,
        headers={
            "X-API-Key": "event-key",
            "Idempotency-Key": "request-2",
        },
    )

    assert second_response.status_code == 200
    assert first_response.json()["id"] == second_response.json()["id"]


@pytest.mark.asyncio
async def test_batch_insert_and_ignore_duplicates(client):
    source_response = await client.post(
        "/api/v1/sources",
        json={
            "name": "batch-source",
            "api_key": "batch-key",
        },
    )

    assert source_response.status_code == 201

    batch_data = {
        "events": [
            {
                "external_id": "batch-1",
                "severity": 3,
                "event_type": "payment_failed",
                "payload": {"order_id": "1"},
                "occurred_at": "2026-08-28T10:00:00Z",
            },
            {
                "external_id": "batch-2",
                "severity": 4,
                "event_type": "payment_failed",
                "payload": {"order_id": "2"},
                "occurred_at": "2026-08-28T10:01:00Z",
            },
        ]
    }

    headers = {
        "X-API-Key": "batch-key",
    }

    first_response = await client.post(
        "/api/v1/events/batch",
        json=batch_data,
        headers=headers,
    )

    assert first_response.status_code == 201
    assert first_response.json() == {"inserted": 2}

    second_response = await client.post(
        "/api/v1/events/batch",
        json=batch_data,
        headers=headers,
    )

    assert second_response.status_code == 201
    assert second_response.json() == {"inserted": 0}


@pytest.mark.asyncio
async def test_batch_rejects_more_than_500_events(client):
    source_response = await client.post(
        "/api/v1/sources",
        json={
            "name": "large-batch-source",
            "api_key": "large-batch-key",
        },
    )

    assert source_response.status_code == 201

    events = [
        {
            "external_id": f"event-{i}",
            "severity": 3,
            "event_type": "payment_failed",
            "payload": {},
            "occurred_at": "2026-08-28T10:00:00Z",
        }
        for i in range(501)
    ]

    response = await client.post(
        "/api/v1/events/batch",
        json={"events": events},
        headers={"X-API-Key": "large-batch-key"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_event_creates_alert_for_matching_rule(client):
    source_response = await client.post(
        "/api/v1/sources",
        json={
            "name": "correlation-source",
            "api_key": "correlation-key",
        },
    )
    assert source_response.status_code == 201

    rule_response = await client.post(
        "/api/v1/rules",
        headers={"X-API-Key": "correlation-key"},
        json={
            "name": "high severity errors",
            "event_type": "error",
            "min_severity": 4,
            "threshold": 1,
            "window_sec": 60,
        },
    )
    assert rule_response.status_code == 201

    event_response = await client.post(
        "/api/v1/events",
        headers={
            "X-API-Key": "correlation-key",
            "Idempotency-Key": "correlation-event-1",
        },
        json={
            "external_id": "correlation-event-1",
            "severity": 5,
            "event_type": "error",
            "payload": {"message": "database unavailable"},
            "occurred_at": datetime.now(UTC).isoformat(),
        },
    )
    assert event_response.status_code == 201

    alerts_response = await client.get(
        "/api/v1/alerts",
        headers={"X-API-Key": "correlation-key"},
    )
    assert alerts_response.status_code == 200

    alerts = alerts_response.json()

    assert len(alerts) == 1
    assert alerts[0]["matched_count"] == 1
    assert alerts[0]["status"] == "open"
