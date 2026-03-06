from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)

def test_validation_error_returns_envelope():
    # Missing required fields (tool_name, input) -> should not be raw 422
    resp = client.post("/tools/invoke", json={"contract_version": "v1"})
    assert resp.status_code == 200

    data = resp.json()
    assert data["contract_version"] == "v1"
    assert data["ok"] is False
    assert data["output"] is None
    assert data["error"]["code"] == "VALIDATION_ERROR"
