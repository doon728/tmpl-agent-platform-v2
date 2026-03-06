from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)

def test_invoke_search_kb():
    payload = {
        "contract_version": "v1",
        "tool_name": "search_kb",
        "input": {"query": "hello"},
        "tenant_id": "t1",
        "user_id": "u1",
        "correlation_id": "c1",
    }
    r = client.post("/tools/invoke", json=payload)
    assert r.status_code == 200

    body = r.json()
    assert body["contract_version"] == "v1"
    assert body["ok"] is True
    assert body["tool_name"] == "search_kb"
    assert "results" in body["output"]
