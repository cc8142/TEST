import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse


class _Handler(BaseHTTPRequestHandler):
    server_version = "DemoServer/1.0"

    def _send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8"))

    def _serve_index(self):
        html = self.server.index_html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(html)))
        self.end_headers()
        self.wfile.write(html)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            return self._serve_index()
        if parsed.path == "/api/health":
            return self._send_json(200, {"status": "ok"})
        if parsed.path.startswith("/api/order/"):
            order_id = parsed.path.split("/")[-1]
            with self.server.lock:
                order = self.server.orders.get(order_id)
            if not order:
                return self._send_json(404, {"error": "not_found"})
            return self._send_json(200, order)
        self.send_error(404, "Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/login":
            payload = self._read_json()
            if payload.get("username") == "demo" and payload.get("password") == "pass":
                return self._send_json(200, {"token": "t-demo"})
            return self._send_json(401, {"error": "invalid_credentials"})
        if parsed.path == "/api/order":
            auth = self.headers.get("Authorization", "")
            if auth != "Bearer t-demo":
                return self._send_json(403, {"error": "unauthorized"})
            payload = self._read_json()
            try:
                price = float(payload.get("price"))
                qty = int(payload.get("qty"))
            except (TypeError, ValueError):
                return self._send_json(400, {"error": "invalid_payload"})
            if price < 0 or qty <= 0:
                return self._send_json(400, {"error": "invalid_payload"})
            if price.is_integer():
                price = int(price)
            total = price * qty
            client_order_id = payload.get("client_order_id")
            idempotency_key = self.headers.get("Idempotency-Key", "")
            with self.server.lock:
                if idempotency_key and idempotency_key in self.server.idempotency_index:
                    order_id = self.server.idempotency_index[idempotency_key]
                    order = self.server.orders.get(order_id)
                    if order:
                        return self._send_json(200, order)
                order_id = client_order_id or f"A{self.server.order_counter}"
                if order_id in self.server.orders:
                    return self._send_json(200, self.server.orders[order_id])
                order = {"order_id": order_id, "total": total, "status": "created"}
                self.server.orders[order_id] = order
                if idempotency_key:
                    self.server.idempotency_index[idempotency_key] = order_id
                if not client_order_id:
                    self.server.order_counter += 1
            return self._send_json(201, order)
        self.send_error(404, "Not Found")

    def do_DELETE(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/order/"):
            order_id = parsed.path.split("/")[-1]
            with self.server.lock:
                order = self.server.orders.pop(order_id, None)
            if not order:
                return self._send_json(404, {"error": "not_found"})
            return self._send_json(200, {"order_id": order_id, "deleted": True})
        self.send_error(404, "Not Found")

    def log_message(self, fmt, *args):
        # Keep logs concise for test output
        return


class DemoServer:
    def __init__(self, host="127.0.0.1", port=0, index_html=None):
        self.host = host
        self.port = port
        self.index_html = index_html or "<html><body>demo</body></html>"
        self._httpd = None
        self._thread = None

    def start(self):
        self._httpd = ThreadingHTTPServer((self.host, self.port), _Handler)
        self._httpd.index_html = self.index_html
        self._httpd.orders = {}
        self._httpd.idempotency_index = {}
        self._httpd.order_counter = 10001
        self._httpd.lock = threading.Lock()
        self.port = self._httpd.server_address[1]
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()

    def stop(self):
        if self._httpd:
            self._httpd.shutdown()
            self._httpd.server_close()

    @property
    def base_url(self):
        return f"http://{self.host}:{self.port}"

