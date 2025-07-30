import pytest
from fastapi.testclient import TestClient
import internal_api
import external_api


class TestAdditionalEndpoints:
    """Extra endpoint coverage for internal and external APIs."""

    def test_internal_debug_storage(self):
        client = TestClient(internal_api.internal_app)
        resp = client.get("/debug/storage")
        assert resp.status_code == 200
        assert "detail" in resp.json()

    def test_external_search_endpoint(self, monkeypatch):
        client = TestClient(external_api.external_app)

        async def fake_verify(*args, **kwargs):
            return {"client_id": "1", "actor_type": "human", "actor_id": "1"}

        async def fake_call(endpoint: str, method: str = "POST", json_data=None):
            return [{"entity": {"name": "Mock"}, "score": 1.0}]

        monkeypatch.setattr(external_api, "verify_external_auth", fake_verify)
        monkeypatch.setattr(external_api, "call_internal_api", fake_call)

        resp = client.post(
            "/memory/search",
            json={"query": "test"},
            headers={"Authorization": "Bearer token"},
        )
        assert resp.status_code == 200
        assert resp.json()[0]["entity"]["name"] == "Mock"

