import os
import uuid


class DataFactory:
    def __init__(self, seed_prefix="demo"):
        env_prefix = os.getenv("TEST_TENANT_PREFIX")
        self.seed_prefix = env_prefix if env_prefix else seed_prefix

    def valid_user(self):
        username = os.getenv("TEST_USERNAME", "demo")
        password = os.getenv("TEST_PASSWORD", "pass")
        return {"username": username, "password": password}

    def invalid_user(self):
        return {
            "username": f"{self.seed_prefix}-{uuid.uuid4().hex[:6]}",
            "password": "invalid",
        }

    def order(self, price=19, qty=2, client_order_id=None):
        payload = {"price": price, "qty": qty}
        if client_order_id:
            payload["client_order_id"] = client_order_id
        return payload

    def tenant(self):
        return f"{self.seed_prefix}-{uuid.uuid4().hex[:8]}"

    def client_order_id(self):
        return f"{self.seed_prefix}-{uuid.uuid4().hex[:8]}"

    def idempotency_key(self):
        return uuid.uuid4().hex

