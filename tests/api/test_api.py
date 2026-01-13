import allure
import pytest

from framework.assertions import assert_schema, assert_status
from framework.allure_utils import attach_json
from tests.api.services.auth_service import AuthService
from tests.api.services.order_service import OrderService


@allure.epic("Commerce Platform")
@allure.feature("Health")
@allure.story("Service readiness")
@allure.severity(allure.severity_level.BLOCKER)
@allure.label("layer", "api")
@allure.label("component", "health")
@pytest.mark.api
@pytest.mark.smoke
def test_health(api_client):
    with allure.step("Call health endpoint"):
        resp = api_client.get("/api/health")
    with allure.step("Validate status and payload"):
        assert_status(resp, 200)
        payload = resp.json()
        assert_schema(payload, {"status": str})
        assert payload["status"] == "ok"


@allure.epic("Commerce Platform")
@allure.feature("Authentication")
@allure.story("Login success")
@allure.severity(allure.severity_level.CRITICAL)
@allure.label("layer", "api")
@allure.label("component", "auth")
@pytest.mark.api
def test_login_success(api_client, data_factory):
    user = data_factory.valid_user()
    attach_json("credentials", {"username": user["username"], "password": "***"})
    with allure.step("Login with valid credentials"):
        resp = AuthService(api_client).login(**user)
    with allure.step("Validate token returned"):
        assert_status(resp, 200)
        payload = resp.json()
        assert_schema(payload, {"token": str})
        assert "token" in payload


@allure.epic("Commerce Platform")
@allure.feature("Authentication")
@allure.story("Login invalid")
@allure.severity(allure.severity_level.NORMAL)
@allure.label("layer", "api")
@allure.label("component", "auth")
@pytest.mark.api
def test_login_invalid(api_client, data_factory):
    user = data_factory.invalid_user()
    attach_json("credentials", {"username": user["username"], "password": "***"})
    with allure.step("Login with invalid credentials"):
        resp = AuthService(api_client).login(**user)
    with allure.step("Validate unauthorized response"):
        assert_status(resp, 401)
        payload = resp.json()
        assert_schema(payload, {"error": str})


@allure.epic("Commerce Platform")
@allure.feature("Orders")
@allure.story("Pricing calculation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.label("layer", "api")
@allure.label("component", "order")
@pytest.mark.api
@pytest.mark.parametrize("price,qty,total", [(19, 2, 38), (10, 1, 10), (0, 3, 0)])
def test_create_order_totals(api_client, data_factory, cleanup_tasks, price, qty, total):
    with allure.step("Login and get token"):
        token = AuthService(api_client).login(**data_factory.valid_user()).json()["token"]
    order_id = data_factory.client_order_id()
    idempotency_key = data_factory.idempotency_key()
    payload = data_factory.order(price=price, qty=qty, client_order_id=order_id)
    attach_json("order_payload", payload)
    with allure.step("Create order"):
        order_service = OrderService(api_client, token=token)
        resp = order_service.create_order(
            price=payload["price"],
            qty=payload["qty"],
            client_order_id=order_id,
            idempotency_key=idempotency_key,
        )
    cleanup_tasks.append(lambda: order_service.delete_order(order_id))
    with allure.step("Validate order total"):
        assert_status(resp, 201)
        response_payload = resp.json()
        assert_schema(response_payload, {"order_id": str, "total": (int, float), "status": str})
        assert response_payload["total"] == total
        assert response_payload["order_id"] == order_id


@allure.epic("Commerce Platform")
@allure.feature("Orders")
@allure.story("Authorization enforcement")
@allure.severity(allure.severity_level.CRITICAL)
@allure.label("layer", "api")
@allure.label("component", "order")
@pytest.mark.api
def test_create_order_requires_auth(api_client):
    with allure.step("Create order without token"):
        order_service = OrderService(api_client)
        resp = order_service.create_order(price=10, qty=1)
    with allure.step("Validate forbidden response"):
        assert_status(resp, 403)
        payload = resp.json()
        assert_schema(payload, {"error": str})


@allure.epic("Commerce Platform")
@allure.feature("Orders")
@allure.story("Payload validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.label("layer", "api")
@allure.label("component", "order")
@pytest.mark.api
def test_create_order_invalid_payload(api_client, data_factory):
    with allure.step("Login and get token"):
        token = AuthService(api_client).login(**data_factory.valid_user()).json()["token"]
    order_id = data_factory.client_order_id()
    idempotency_key = data_factory.idempotency_key()
    payload = data_factory.order(price=-1, qty=0, client_order_id=order_id)
    attach_json("order_payload", payload)
    with allure.step("Create invalid order"):
        order_service = OrderService(api_client, token=token)
        resp = order_service.create_order(
            price=payload["price"],
            qty=payload["qty"],
            client_order_id=order_id,
            idempotency_key=idempotency_key,
        )
    with allure.step("Validate bad request response"):
        assert_status(resp, 400)
        response_payload = resp.json()
        assert_schema(response_payload, {"error": str})


@allure.epic("Commerce Platform")
@allure.feature("Orders")
@allure.story("Order lookup")
@allure.severity(allure.severity_level.NORMAL)
@allure.label("layer", "api")
@allure.label("component", "order")
@pytest.mark.api
def test_get_order_by_id(api_client, data_factory, cleanup_tasks):
    with allure.step("Login and get token"):
        token = AuthService(api_client).login(**data_factory.valid_user()).json()["token"]
    order_service = OrderService(api_client, token=token)
    order_id = data_factory.client_order_id()
    with allure.step("Create order"):
        resp = order_service.create_order(price=10, qty=1, client_order_id=order_id)
    cleanup_tasks.append(lambda: order_service.delete_order(order_id))
    assert_status(resp, 201)
    with allure.step("Fetch order by id"):
        resp = order_service.get_order(order_id)
    with allure.step("Validate order status"):
        assert_status(resp, 200)
        payload = resp.json()
        assert_schema(payload, {"order_id": str, "status": str, "total": (int, float)})
        assert payload["status"] == "created"

