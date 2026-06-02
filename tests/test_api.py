"""Test API endpoints: health check / datasets"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from backend.api import app


client = TestClient(app)


class TestHealth:
    def test_health_check(self):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["version"] == "0.3.5"

    def test_healthz(self):
        resp = client.get("/healthz")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_ready_check(self):
        resp = client.get("/api/ready")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ready"] is True


class TestDatasets:
    def test_list_datasets(self):
        resp = client.get("/api/data/datasets")
        assert resp.status_code == 200
        data = resp.json()
        assert "datasets" in data
        assert isinstance(data["datasets"], list)

    def test_upload_csv(self):
        csv_content = "name,age\nAlice,25\nBob,30"
        resp = client.post("/api/data/upload", files={
            "file": ("test.csv", csv_content.encode(), "text/csv"),
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["rows"] == 2
        assert data["columns"] == ["name", "age"]

    def test_upload_invalid_ext(self):
        resp = client.post("/api/data/upload", files={
            "file": ("test.txt", b"not data", "text/plain"),
        })
        assert resp.status_code == 400
