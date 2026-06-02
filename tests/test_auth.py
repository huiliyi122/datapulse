"""测试认证系统: JWT 生成/验证/撤销"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from auth import create_jwt, verify_jwt, user_store, hash_password, verify_password


class TestPasswordHashing:
    def test_hash_and_verify(self):
        pw = "test-password-123"
        hashed = hash_password(pw)
        assert verify_password(pw, hashed)
        assert not verify_password("wrong", hashed)

    def test_hash_is_salted(self):
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2  # 不同盐值产生不同哈希
        assert verify_password("same", h1)
        assert verify_password("same", h2)

    def test_bad_hash_handled(self):
        assert not verify_password("anything", "bad-format")
        assert not verify_password("anything", "")


class TestJWT:
    def test_create_and_verify(self):
        token = create_jwt(1, "testuser")
        payload = verify_jwt(token)
        assert payload is not None
        assert payload["user_id"] == 1
        assert payload["username"] == "testuser"

    def test_verify_invalid_token(self):
        assert verify_jwt("not.a.token") is None
        assert verify_jwt("") is None

    def test_verify_tampered_token(self):
        token = create_jwt(1, "testuser")
        # 修改 payload 部分
        parts = token.split(".")
        tampered = f"{parts[0]}.{parts[1]}.badtoken"
        assert verify_jwt(tampered) is None


class TestUserStore:
    def test_create_and_verify(self):
        store = user_store  # 全局单例
        user = store.create_user("_testuser_api", "test@test.com", "testpass123")
        if user is None:
            # 如果用户已存在，直接验证
            found = store.get_user("_testuser_api")
            assert found is not None
            verified = store.verify_user("_testuser_api", "testpass123")
            assert verified is not None
        else:
            assert user["username"] == "_testuser_api"
            verified = store.verify_user("_testuser_api", "testpass123")
            assert verified is not None
            assert verified["id"] == user["id"]

    def test_token_save_verify_revoke(self):
        token = "test_token_jwt_abc123"
        user = user_store.get_user("admin")
        assert user is not None, "admin user should exist from ensure_default_admin"

        user_store.save_token(user["id"], token)
        uid = user_store.verify_token(token)
        assert uid == user["id"]

        user_store.revoke_token(token)
        assert user_store.verify_token(token) is None
