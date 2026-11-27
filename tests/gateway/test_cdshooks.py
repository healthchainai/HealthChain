import pytest
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from healthchain.gateway.cds import CDSHooksConfig
from healthchain.gateway.cds import (
    CDSHooksService,
)
from healthchain.gateway.events.dispatcher import EventDispatcher
from healthchain.models.requests.cdsrequest import CDSRequest
from healthchain.models.responses.cdsresponse import CDSResponse, Card
from healthchain.models.responses.cdsdiscovery import CDSServiceInformation


@pytest.mark.parametrize(
    "config_args,expected_paths",
    [
        # Default config
        (
            {},
            {
                "base_path": "/cds",
                "discovery_path": "/cds-discovery",
                "service_path": "/cds-services",
            },
        ),
        # Custom config
        (
            {
                "base_path": "/custom-cds",
                "discovery_path": "/custom-discovery",
                "service_path": "/custom-services",
            },
            {
                "base_path": "/custom-cds",
                "discovery_path": "/custom-discovery",
                "service_path": "/custom-services",
            },
        ),
    ],
)
def test_cdshooks_service_configuration(config_args, expected_paths):
    """CDSHooksService supports both default and custom path configurations."""
    if config_args:
        config = CDSHooksConfig(**config_args)
        gateway = CDSHooksService(config=config)
    else:
        gateway = CDSHooksService.create()

    assert isinstance(gateway, CDSHooksService)
    assert isinstance(gateway.config, CDSHooksConfig)
    assert gateway.config.system_type == "CDS-HOOKS"

    for path_name, expected_value in expected_paths.items():
        assert getattr(gateway.config, path_name) == expected_value


def test_cdshooks_hook_decorator_with_metadata_variants(test_cds_request):
    """Hook decorator supports default and custom metadata configurations."""
    gateway = CDSHooksService()
    calls = []

    # Default metadata
    @gateway.hook("patient-view", id="test-patient-view")
    def handle_patient_view_default(request):
        calls.append("patient-view")
        return CDSResponse(cards=[])

    # Custom metadata; the id equals another service's hook type
    @gateway.hook(
        "order-select",
        id="patient-view",
        title="Custom Title",
        description="Custom description",
        usage_requirements="Requires patient context",
    )
    def handle_order_select_custom(request):
        calls.append("order-select")
        return CDSResponse(cards=[])

    # Registry is keyed by service id; capabilities list hook types
    assert set(gateway._handlers) == {"test-patient-view", "patient-view"}
    assert gateway.get_capabilities() == ["order-select", "patient-view"]

    # Check default metadata
    default_meta = gateway._handler_metadata["test-patient-view"]
    assert default_meta["hook"] == "patient-view"
    assert default_meta["title"] == "Patient View"
    assert default_meta["description"] == "CDS Hook service created by HealthChain"

    # Check custom metadata
    custom_meta = gateway._handler_metadata["patient-view"]
    assert custom_meta["hook"] == "order-select"
    assert custom_meta["title"] == "Custom Title"
    assert custom_meta["description"] == "Custom description"
    assert custom_meta["usage_requirements"] == "Requires patient context"

    # Hook-type calls never match ids, and id calls never match hook types
    order_select_request = test_cds_request.model_copy(update={"hook": "order-select"})
    gateway.handle_request(test_cds_request)
    gateway.handle_request(order_select_request, service_id="patient-view")
    assert calls == ["patient-view", "order-select"]
    calls.clear()

    # A service never runs on a request for another hook type
    with pytest.raises(ValueError, match="serves 'order-select', got 'patient-view'"):
        gateway.handle_request(test_cds_request, service_id="patient-view")
    with pytest.raises(ValueError, match="serves 'order-select', got 'patient-view'"):
        gateway.dispatch("order-select", request=test_cds_request)
    assert calls == []

    # A request for another hook type is rejected by this route, even when served elsewhere
    app = FastAPI()
    app.include_router(gateway)
    body = test_cds_request.model_dump(mode="json", exclude_none=True)
    body["hook"] = "order-select"
    response = TestClient(app).post("/cds/cds-services/test-patient-view", json=body)
    assert response.status_code == 400
    assert calls == []


def test_cdshooks_gateway_handle_request(test_cds_request):
    """Test request handler endpoint"""
    gateway = CDSHooksService()

    # Register a handler with the hook decorator
    @gateway.hook("patient-view", id="test-patient-view")
    def handle_patient_view(request):
        return CDSResponse(
            cards=[
                Card(
                    summary="Test response", indicator="info", source={"label": "Test"}
                )
            ]
        )

    # Handle request
    result = gateway.handle_request(test_cds_request)
    assert isinstance(result, CDSResponse)
    assert len(result.cards) == 1
    assert result.cards[0].summary == "Test response"

    # Direct callers see errors instead of empty cards
    with pytest.raises(ValidationError):
        gateway.dispatch("patient-view", context={})
    with pytest.raises(ValueError, match="No handler registered"):
        gateway.dispatch("order-sign", request=test_cds_request)


def _raise(exc):
    raise exc


@pytest.mark.parametrize(
    "outcome,expected_status,expected_detail",
    [
        (
            lambda: _raise(ValueError("secret-patient-123")),
            500,
            "CDS service 'test-patient-view' failed: ValueError",
        ),
        (
            lambda: _raise(StarletteHTTPException(412, "missing prefetch")),
            412,
            "missing prefetch",
        ),
        (lambda: CDSResponse(cards=[]), 200, None),
        (
            lambda: None,
            500,
            "CDS service 'test-patient-view' failed: TypeError",
        ),
        (
            lambda: {"cards": [{}]},
            500,
            "CDS service 'test-patient-view' failed: ValidationError",
        ),
    ],
    ids=["raises", "http-412", "no-cards", "returns-none", "invalid-dict"],
)
def test_cdshooks_http_status_for_handler_outcomes(
    test_cds_request, outcome, expected_status, expected_detail
):
    """Hook route maps handler outcomes to HTTP status without HealthChainAPI."""
    gateway = CDSHooksService()

    @gateway.hook("patient-view", id="test-patient-view")
    def handle_patient_view(request):
        return outcome()

    app = FastAPI()
    app.include_router(gateway)
    client = TestClient(app, raise_server_exceptions=False)

    response = client.post(
        "/cds/cds-services/test-patient-view",
        json=test_cds_request.model_dump(mode="json", exclude_none=True),
    )

    assert response.status_code == expected_status
    if expected_detail is None:
        assert response.json() == {"cards": []}
    else:
        assert response.json()["detail"] == expected_detail
    assert "secret-patient-123" not in response.text


def test_cdshooks_gateway_handle_discovery():
    """Test discovery endpoint handler"""
    gateway = CDSHooksService()

    # Register sample hooks
    @gateway.hook("patient-view", id="test-patient-view", title="Patient View")
    def handle_patient_view(request):
        return CDSResponse(cards=[])

    @gateway.hook("order-select", id="test-order-select", title="Order Select")
    def handle_order_select(request):
        return CDSResponse(cards=[])

    # Get discovery response
    result = gateway.handle_discovery()
    assert isinstance(result, CDSServiceInformation)
    assert len(result.services) == 2

    # Check if hook information is correctly included
    hooks = {s.hook: s for s in result.services}
    assert "patient-view" in hooks
    assert hooks["patient-view"].id == "test-patient-view"
    assert hooks["patient-view"].title == "Patient View"

    assert "order-select" in hooks
    assert hooks["order-select"].id == "test-order-select"
    assert hooks["order-select"].title == "Order Select"


def test_cdshooks_gateway_routing_and_custom_paths(test_cds_request):
    """Services sharing a hook type each run at their own route, keyed by id."""

    def _card_response(summary):
        return CDSResponse(
            cards=[Card(summary=summary, indicator="info", source={"label": "Test"})]
        )

    # Test default paths: two services serve the same hook type
    gateway = CDSHooksService()

    @gateway.hook("patient-view", id="allergies", title="Allergies")
    def handle_allergies(request):
        return _card_response("allergies")

    @gateway.hook("patient-view", id="sepsis", title="Sepsis")
    def handle_sepsis(request):
        return _card_response("sepsis")

    app = FastAPI()
    app.include_router(gateway)
    client = TestClient(app)
    body = test_cds_request.model_dump(mode="json", exclude_none=True)

    def summary_at(service_id):
        response = client.post(f"/cds/cds-services/{service_id}", json=body)
        assert response.status_code == 200
        return response.json()["cards"][0]["summary"]

    assert summary_at("allergies") == "allergies"
    assert summary_at("sepsis") == "sepsis"

    discovery = client.get("/cds/cds-discovery").json()
    assert [(s["id"], s["hook"], s["title"]) for s in discovery["services"]] == [
        ("allergies", "patient-view", "Allergies"),
        ("sepsis", "patient-view", "Sepsis"),
    ]

    # Direct calls by hook type refuse to pick one of several services
    with pytest.raises(ValueError, match="allergies, sepsis"):
        gateway.dispatch("patient-view", request=test_cds_request)
    with pytest.raises(ValueError, match="allergies, sepsis"):
        gateway.handle_request(test_cds_request)
    result = gateway.handle_request(test_cds_request, service_id="sepsis")
    assert result.cards[0].summary == "sepsis"

    # Duplicate ids and register_handler() are rejected without changing anything
    route_count = len(gateway.routes)
    handlers = dict(gateway._handlers)
    with pytest.raises(ValueError, match="'allergies' is already registered"):

        @gateway.hook("patient-view", id="allergies")
        def handle_duplicate(request):
            return _card_response("duplicate")

    for service_id in ("fresh-id", "allergies"):
        with pytest.raises(TypeError, match=r"hook\("):
            gateway.register_handler(service_id, lambda request: None)

    assert len(gateway.routes) == route_count
    assert gateway._handlers == handlers
    assert client.get("/cds/cds-discovery").json() == discovery
    assert summary_at("allergies") == "allergies"

    # Test custom paths
    custom_config = CDSHooksConfig(
        base_path="/custom-cds",
        discovery_path="/custom-discovery",
        service_path="/custom-services",
    )
    custom_gateway = CDSHooksService(config=custom_config)

    @custom_gateway.hook("patient-view", id="test-service")
    def handle_custom_patient_view(request):
        return CDSResponse(cards=[])

    # Verify custom gateway has correct prefix
    assert custom_gateway.prefix == "/custom-cds"

    # Verify routes exist
    custom_route_paths = [route.path for route in custom_gateway.routes]
    assert any("custom-discovery" in path for path in custom_route_paths)
    assert any("test-service" in path for path in custom_route_paths)


def test_cdshooks_gateway_event_emission():
    """Test that events are emitted when handling requests"""
    # Create mock event dispatcher
    mock_dispatcher = MagicMock(spec=EventDispatcher)

    # Create gateway with event dispatcher
    gateway = CDSHooksService(event_dispatcher=mock_dispatcher)

    # Register a handler
    @gateway.hook("patient-view", id="test-service")
    def handle_patient_view(request):
        return CDSResponse(
            cards=[
                Card(summary="Test card", indicator="info", source={"label": "Test"})
            ]
        )

    # Create a test request
    request = CDSRequest(
        hook="patient-view",
        hookInstance="test-instance",
        context={"patientId": "123", "userId": "456"},
    )

    # Handle the request
    gateway.handle_request(request)

    assert mock_dispatcher.emit.called


def test_cdshooks_gateway_hook_invalid_hook_type():
    """Test hook decorator with invalid hook type"""
    gateway = CDSHooksService()

    # Try to register an invalid hook type
    with pytest.raises(ValueError):

        @gateway.hook("invalid-hook-type", id="test")
        def handle_invalid(request):
            return CDSResponse(cards=[])
