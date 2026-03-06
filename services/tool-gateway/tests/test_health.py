from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["contract_version"] == "v1"
