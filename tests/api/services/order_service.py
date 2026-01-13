class OrderService:
    def __init__(self, client, token=None):
        self.client = client
        self.token = token

    def create_order(self, price, qty, client_order_id=None, idempotency_key=None):
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        payload = {"price": price, "qty": qty}
        if client_order_id:
            payload["client_order_id"] = client_order_id
        return self.client.post(
            "/api/order",
            json=payload,
            headers=headers,
        )

    def get_order(self, order_id):
        return self.client.get(f"/api/order/{order_id}")

    def delete_order(self, order_id):
        return self.client.request("DELETE", f"/api/order/{order_id}")

