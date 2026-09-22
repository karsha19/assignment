def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def create_camera(client, admin_token, code="C001"):
    payload = {
        "camera_code": code,
        "name": "Test Camera",
        "latitude": 23.02,
        "longitude": 72.57,
        "source_protocol": "recorded",
        "stream_reference": "/media/sample/test.mp4",
    }
    resp = client.post("/api/v1/cameras", json=payload, headers=auth_header(admin_token))
    return resp.json()["id"]


def create_watchlist_record(client, admin_token, identifier="GJ01XX0001"):
    payload = {
        "entity_type": "stolen_vehicle",
        "identifier": identifier,
        "display_name": "Test stolen vehicle",
        "reason": "unit test",
    }
    resp = client.post("/api/v1/watchlist", json=payload, headers=auth_header(admin_token))
    return resp.json()


def test_identifier_normalization_matches_variants(client, admin_token, operator_token):
    camera_id = create_camera(client, admin_token)
    create_watchlist_record(client, admin_token, identifier="GJ01XX0001")

    event_payload = {
        "idempotency_key": "evt-norm-1",
        "camera_id": camera_id,
        "event_type": "anpr",
        "entity_identifier": "gj-01 xx-0001",
        "confidence": 0.9,
        "event_timestamp": "2026-01-01T10:00:00",
    }
    resp = client.post("/api/v1/analytics/events", json=event_payload, headers=auth_header(operator_token))
    assert resp.status_code == 201

    alerts = client.get("/api/v1/alerts", headers=auth_header(operator_token)).json()
    assert len(alerts) == 1
    assert alerts[0]["matched_identifier"] == "gj-01 xx-0001"


def test_nonmatching_event_creates_no_alert(client, admin_token, operator_token):
    camera_id = create_camera(client, admin_token)
    create_watchlist_record(client, admin_token, identifier="GJ01XX0001")

    event_payload = {
        "idempotency_key": "evt-nomatch-1",
        "camera_id": camera_id,
        "event_type": "anpr",
        "entity_identifier": "GJ09ZZ9999",
        "confidence": 0.9,
        "event_timestamp": "2026-01-01T10:00:00",
    }
    resp = client.post("/api/v1/analytics/events", json=event_payload, headers=auth_header(operator_token))
    assert resp.status_code == 201

    alerts = client.get("/api/v1/alerts", headers=auth_header(operator_token)).json()
    assert len(alerts) == 0


def test_duplicate_event_rejected(client, admin_token, operator_token):
    camera_id = create_camera(client, admin_token)
    event_payload = {
        "idempotency_key": "evt-dup-1",
        "camera_id": camera_id,
        "event_type": "anpr",
        "entity_identifier": "GJ01AB1234",
        "confidence": 0.9,
        "event_timestamp": "2026-01-01T10:00:00",
    }
    first = client.post("/api/v1/analytics/events", json=event_payload, headers=auth_header(operator_token))
    assert first.status_code == 201
    second = client.post("/api/v1/analytics/events", json=event_payload, headers=auth_header(operator_token))
    assert second.status_code == 409


def test_anpr_event_requires_identifier(client, admin_token, operator_token):
    camera_id = create_camera(client, admin_token)
    event_payload = {
        "idempotency_key": "evt-noident-1",
        "camera_id": camera_id,
        "event_type": "anpr",
        "confidence": 0.9,
        "event_timestamp": "2026-01-01T10:00:00",
    }
    resp = client.post("/api/v1/analytics/events", json=event_payload, headers=auth_header(operator_token))
    assert resp.status_code == 422


def test_disabled_watchlist_record_does_not_alert(client, admin_token, operator_token):
    camera_id = create_camera(client, admin_token)
    record = create_watchlist_record(client, admin_token, identifier="GJ01XX0001")
    client.post(f"/api/v1/watchlist/{record['id']}/disable", headers=auth_header(admin_token))

    event_payload = {
        "idempotency_key": "evt-disabled-wl",
        "camera_id": camera_id,
        "event_type": "anpr",
        "entity_identifier": "GJ01XX0001",
        "confidence": 0.9,
        "event_timestamp": "2026-01-01T10:00:00",
    }
    client.post("/api/v1/analytics/events", json=event_payload, headers=auth_header(operator_token))
    alerts = client.get("/api/v1/alerts", headers=auth_header(operator_token)).json()
    assert len(alerts) == 0


def test_alert_lifecycle_transitions(client, admin_token, operator_token):
    camera_id = create_camera(client, admin_token)
    create_watchlist_record(client, admin_token, identifier="GJ01XX0001")
    event_payload = {
        "idempotency_key": "evt-lifecycle-1",
        "camera_id": camera_id,
        "event_type": "anpr",
        "entity_identifier": "GJ01XX0001",
        "confidence": 0.9,
        "event_timestamp": "2026-01-01T10:00:00",
    }
    client.post("/api/v1/analytics/events", json=event_payload, headers=auth_header(operator_token))
    alert = client.get("/api/v1/alerts", headers=auth_header(operator_token)).json()[0]

    ack = client.post(f"/api/v1/alerts/{alert['id']}/acknowledge", headers=auth_header(operator_token))
    assert ack.status_code == 200
    assert ack.json()["status"] == "acknowledged"

    ack2 = client.post(f"/api/v1/alerts/{alert['id']}/acknowledge", headers=auth_header(operator_token))
    assert ack2.status_code == 409

    resolve = client.post(f"/api/v1/alerts/{alert['id']}/resolve", headers=auth_header(operator_token))
    assert resolve.status_code == 200
    assert resolve.json()["status"] == "resolved"


def test_movement_history_orders_chronologically(client, admin_token, operator_token):
    cam1 = create_camera(client, admin_token, "C001")
    cam2 = create_camera(client, admin_token, "C002")
    identifier = "GJ01XX0001"

    events = [
        (cam1, "2026-01-01T10:41:00", "evt-m3"),
        (cam2, "2026-01-01T10:02:00", "evt-m1"),
        (cam1, "2026-01-01T10:18:00", "evt-m2"),
    ]
    for camera_id, ts, key in events:
        payload = {
            "idempotency_key": key,
            "camera_id": camera_id,
            "event_type": "anpr",
            "entity_identifier": identifier,
            "confidence": 0.9,
            "event_timestamp": ts,
        }
        client.post("/api/v1/analytics/events", json=payload, headers=auth_header(operator_token))

    resp = client.get(f"/api/v1/entities/{identifier}/movement-history", headers=auth_header(operator_token))
    assert resp.status_code == 200
    body = resp.json()
    timestamps = [e["timestamp"] for e in body["events"]]
    assert timestamps == sorted(timestamps)
    assert len(body["events"]) == 3
