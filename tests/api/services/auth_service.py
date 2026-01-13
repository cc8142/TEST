class AuthService:
    def __init__(self, client):
        self.client = client

    def login(self, username, password):
        return self.client.post(
            "/api/login",
            json={"username": username, "password": password},
        )
