def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def make_camera_payload(code="C001"):
    return {
        "camera_code": code,
        "name": "Test Camera",
        "department": "Traffic Police",
        "zone": "Zone-1",
        "latitude": 23.02,
        "longitude": 72.57,
        "camera_type": "fixed_junction",
        "source_protocol": "recorded",
        "stream_reference": "/media/sample/test.mp4",
    }


def test_operator_cannot_create_camera(client, operator_token):
    resp = client.post("/api/v1/cameras", json=make_camera_payload(), headers=auth_header(operator_token))
    assert resp.status_code == 403


def test_admin_can_create_camera(client, admin_token):
    resp = client.post("/api/v1/cameras", json=make_camera_payload(), headers=auth_header(admin_token))
    assert resp.status_code == 201
    body = resp.json()
    assert body["camera_code"] == "C001"
    assert body["status"] == "offline"


def test_duplicate_camera_code_rejected(client, admin_token):
    client.post("/api/v1/cameras", json=make_camera_payload(), headers=auth_header(admin_token))
    resp = client.post("/api/v1/cameras", json=make_camera_payload(), headers=auth_header(admin_token))
    assert resp.status_code == 409


def test_invalid_latitude_rejected(client, admin_token):
    payload = make_camera_payload()
    payload["latitude"] = 999
    resp = client.post("/api/v1/cameras", json=payload, headers=auth_header(admin_token))
    assert resp.status_code == 422


def test_disable_camera_prevents_events(client, admin_token, operator_token):
    create = client.post("/api/v1/cameras", json=make_camera_payload(), headers=auth_header(admin_token))
    camera_id = create.json()["id"]

    client.post(f"/api/v1/cameras/{camera_id}/disable", headers=auth_header(admin_token))

    event_payload = {
        "idempotency_key": "evt-1",
        "camera_id": camera_id,
        "event_type": "anpr",
        "entity_identifier": "GJ01AB1234",
        "confidence": 0.9,
        "event_timestamp": "2026-01-01T10:00:00",
    }
    resp = client.post("/api/v1/analytics/events", json=event_payload, headers=auth_header(operator_token))
    assert resp.status_code == 422


def test_camera_search_by_code(client, admin_token):
    client.post("/api/v1/cameras", json=make_camera_payload("C001"), headers=auth_header(admin_token))
    client.post("/api/v1/cameras", json=make_camera_payload("C002"), headers=auth_header(admin_token))
    resp = client.get("/api/v1/cameras?q=C001", headers=auth_header(admin_token))
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 1
    assert results[0]["camera_code"] == "C001"
