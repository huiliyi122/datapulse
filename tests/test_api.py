"""测试 API 端点: 健康检查 / 数据集 / 认证"""
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
        assert data["version"] == "0.3.4"

    def test_healthz(self):
        resp = client.get("/healthz")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_ready_check(self):
        resp = client.get("/api/ready")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ready"] is True


class TestAuth:
    def test_register(self):
        resp = client.post("/api/auth/register", json={
            "username": "_apitest", "email": "apitest@test.com", "password": "testpass123",
        })
        # 可能成功创建或已存在
        assert resp.status_code in (200, 400)

    def test_login_success(self):
        resp = client.post("/api/auth/login", json={
            "username": "admin", "password": "admin123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_failure(self):
        resp = client.post("/api/auth/login", json={
            "username": "admin", "password": "wrongpassword",
        })
        assert resp.status_code == 401

    def test_me_without_token(self):
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401

    def test_me_with_token(self):
        login_resp = client.post("/api/auth/login", json={
            "username": "admin", "password": "admin123",
        })
        token = login_resp.json()["access_token"]

        resp = client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {token}",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "admin"

    def test_logout(self):
        login_resp = client.post("/api/auth/login", json={
            "username": "admin", "password": "admin123",
        })
        token = login_resp.json()["access_token"]

        # 登出
        resp = client.post("/api/auth/logout", headers={
            "Authorization": f"Bearer {token}",
        })
        assert resp.status_code == 200

        # 登出后 token 应无效
        resp = client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {token}",
        })
        assert resp.status_code == 401


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
