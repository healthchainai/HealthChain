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

    # Custom metadata
    @gateway.hook(
        "order-select",
        id="custom-id",
        title="Custom Title",
        description="Custom description",
        usage_requirements="Requires patient context",
    )
    def handle_order_select_custom(request):
        calls.append("order-select")
        return CDSResponse(cards=[])

    # Verify both handlers registered correctly
    assert "patient-view" in gateway._handlers
    assert "order-select" in gateway._handlers

    # Check default metadata
    default_meta = gateway._handler_metadata["patient-view"]
    assert default_meta["id"] == "test-patient-view"
    assert default_meta["title"] == "Patient View"
    assert default_meta["description"] == "CDS Hook service created by HealthChain"

    # Check custom metadata
    custom_meta = gateway._handler_metadata["order-select"]
    assert custom_meta["id"] == "custom-id"
    assert custom_meta["title"] == "Custom Title"
    assert custom_meta["description"] == "Custom description"
    assert custom_meta["usage_requirements"] == "Requires patient context"

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


def test_cdshooks_gateway_routing_and_custom_paths():
    """CDSHooksService works as APIRouter with correct route registration."""
    # Test default paths
    gateway = CDSHooksService()

    @gateway.hook("patient-view", id="test-patient-view")
    def handle_patient_view(request):
        return CDSResponse(cards=[])

    # Verify gateway is now an APIRouter
    from fastapi import APIRouter

    assert isinstance(gateway, APIRouter)

    # Verify routes are registered directly in the router
    assert hasattr(gateway, "routes")
    assert len(gateway.routes) >= 2

    # Check that routes have been registered
    route_paths = [route.path for route in gateway.routes]
    route_methods = [list(route.methods)[0] for route in gateway.routes]

    # Should have discovery endpoint
    assert any("cds-discovery" in path for path in route_paths)
    assert "GET" in route_methods

    # Should have hook service endpoint
    assert any("test-patient-view" in path for path in route_paths)
    assert "POST" in route_methods

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

    # Verify get_routes() method no longer exists
    assert not hasattr(gateway, "get_routes")


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
