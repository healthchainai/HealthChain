import pytest
from unittest.mock import AsyncMock, Mock, patch
from typing import Dict, Any

import httpx

from fhir.resources.patient import Patient
from fhir.resources.bundle import Bundle

from healthchain.gateway.clients.fhir.aio.client import AsyncFHIRClient
from healthchain.gateway.clients.fhir.base import FHIRAuthConfig
from healthchain.fhir import FHIRValidationError, load_bundle
from healthchain.gateway.fhir import AsyncFHIRGateway


class MockConnectionManager:
    """Mock FHIR connection manager for testing."""

    def __init__(self):
        self.sources = {"test_source": Mock()}

    def add_source(self, name: str, connection_string: str) -> None:
        self.sources[name] = Mock()

    async def get_client(self, source: str = None):
        return AsyncMock()

    def get_pool_status(self) -> Dict[str, Any]:
        return {
            "max_connections": 100,
            "sources": {"test_source": "connected"},
        }

    async def close(self) -> None:
        pass


@pytest.fixture
def mock_connection_manager():
    """Fixture providing a mock connection manager."""
    return MockConnectionManager()


@pytest.fixture
def fhir_gateway(mock_connection_manager):
    """Fixture providing a AsyncFHIRGateway with mocked dependencies."""
    with patch(
        "healthchain.gateway.clients.fhir.sync.connection.FHIRConnectionManager",
        return_value=mock_connection_manager,
    ):
        return AsyncFHIRGateway(use_events=False)


@pytest.fixture
def test_patient():
    """Fixture providing a test Patient resource."""
    return Patient(id="123", active=True)


@pytest.mark.asyncio
async def test_read_operation_with_client_delegation(fhir_gateway, test_patient):
    """Read operation delegates to client and handles results correctly."""
    with patch.object(
        fhir_gateway, "_execute_with_client", return_value=test_patient
    ) as mock_execute:
        result = await fhir_gateway.read(Patient, "123", "test_source")

        mock_execute.assert_called_once_with(
            "read",
            source="test_source",
            resource_type=Patient,
            resource_id="123",
            client_args=(Patient, "123"),
        )
        assert result == test_patient


@pytest.mark.asyncio
async def test_read_operation_raises_on_not_found(fhir_gateway):
    """Read operation raises ValueError when resource not found."""
    with patch.object(fhir_gateway, "_execute_with_client", return_value=None):
        with pytest.raises(ValueError, match="Resource Patient/123 not found"):
            await fhir_gateway.read(Patient, "123")


@pytest.mark.asyncio
async def test_create_operation_with_validation(fhir_gateway, test_patient):
    """Create operation validates input and returns created resource."""
    created_patient = Patient(id="456", active=True)
    with patch.object(
        fhir_gateway, "_execute_with_client", return_value=created_patient
    ) as mock_execute:
        result = await fhir_gateway.create(test_patient)

        mock_execute.assert_called_once_with(
            "create",
            source=None,
            resource_type=Patient,
            client_args=(test_patient,),
        )
        assert result == created_patient


@pytest.mark.asyncio
async def test_update_operation_requires_resource_id(fhir_gateway):
    """Update operation validates that resource has ID."""
    patient_without_id = Patient(active=True)  # No ID

    with pytest.raises(ValueError, match="Resource must have an ID for update"):
        await fhir_gateway.update(patient_without_id)


@pytest.mark.asyncio
async def test_search_operation_with_parameters(fhir_gateway):
    """Search operation passes parameters correctly to client."""
    mock_bundle = Bundle(type="searchset", total=1)
    params = {"name": "Smith", "active": "true"}

    with patch.object(
        fhir_gateway, "_execute_with_client", return_value=mock_bundle
    ) as mock_execute:
        result = await fhir_gateway.search(Patient, params, "test_source")

        mock_execute.assert_called_once_with(
            "search",
            source="test_source",
            resource_type=Patient,
            client_args=(Patient,),
            client_kwargs={"params": params},
        )
        assert result == mock_bundle


BAD_GENDER = {"gender": "bogus"}
UNKNOWN_FIELD = {"unknownField": "pt-4041"}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "bad_page, bad_fields, validate, expected_expression",
    [
        # Valid results pass the check
        (None, {}, True, None),
        # Binding issue on page 2: only checked with validate=True, on the merged
        # Bundle, so the entry index counts across pages
        (2, BAD_GENDER, True, "Bundle.entry[1].resource.gender"),
        (2, BAD_GENDER, False, None),
        # Page 1 that fails to parse: always raises, with that page's report
        (1, UNKNOWN_FIELD, False, "Bundle.entry[0].resource.unknownField"),
    ],
)
async def test_search_with_pagination(
    fhir_gateway, bad_page, bad_fields, validate, expected_expression
):
    """AsyncFHIRGateway.search fetches each next link exactly as the server wrote it."""
    query = (
        "_tag=https%3A%2F%2Fexample.org%2Fdemo%7Csite-a"
        "&date=ge2024-01-01&date=le2024-12-31&cursor=abc%3D%3D&state=x=y"
    )
    next_link = f"https://fhir.example.org/R4/Patient?{query}"
    seen = []
    pages = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.url.raw_path.decode())
        patient = {"resourceType": "Patient", "id": str(len(seen))}
        if len(seen) == bad_page:
            patient.update(bad_fields)
        bundle = {
            "resourceType": "Bundle",
            "type": "searchset",
            "entry": [{"resource": patient}],
        }
        if len(seen) == 1:
            bundle["link"] = [{"relation": "next", "url": next_link}]
        pages.append(bundle)
        return httpx.Response(200, json=bundle)

    # The async client always builds a token manager, so give it dummy OAuth
    # fields and stub the headers so no token request is made
    client = AsyncFHIRClient(
        FHIRAuthConfig(
            base_url="https://fhir.example.org/R4",
            client_id="test",
            client_secret="test",
            token_url="https://auth.example.org/token",
        ),
        transport=httpx.MockTransport(handler),
    )

    with (
        patch.object(
            client, "_get_headers", AsyncMock(return_value=client.base_headers)
        ),
        patch.object(
            fhir_gateway.connection_manager,
            "get_client",
            AsyncMock(return_value=client),
        ),
    ):
        if expected_expression is None:
            result = await fhir_gateway.search(
                Patient, {"name": "Smith"}, follow_pagination=True, validate=validate
            )
            assert seen == ["/R4/Patient?name=Smith", f"/R4/Patient?{query}"]
            assert [entry.resource.id for entry in result.entry] == ["1", "2"]
            return

        with pytest.raises(FHIRValidationError) as exc_info:
            await fhir_gateway.search(
                Patient, {"name": "Smith"}, follow_pagination=True, validate=validate
            )

    if bad_page == 1:
        # The search stops at the page that failed to parse
        expected_source = pages[0]
    else:
        # The merged Bundle: page 2 carrying the entries of both pages
        expected_source = {**pages[1], "entry": pages[0]["entry"] + pages[1]["entry"]}
    with pytest.raises(FHIRValidationError) as expected:
        load_bundle(expected_source, version="R4B")
    assert exc_info.value.report == expected.value.report
    assert [issue.expression for issue in exc_info.value.report.issues] == [
        expected_expression
    ]


@pytest.mark.asyncio
async def test_search_with_max_pages(fhir_gateway):
    """AsyncFHIRGateway.search respects maximum page limit."""
    page1 = Bundle(
        type="searchset",
        entry=[{"resource": Patient(id="1")}],
        link=[{"relation": "next", "url": "Patient?page=2"}],
    )
    page2 = Bundle(
        type="searchset",
        entry=[{"resource": Patient(id="2")}],
        link=[{"relation": "next", "url": "Patient?page=3"}],
    )

    with patch.object(
        fhir_gateway, "_execute_with_client", side_effect=[page1, page2]
    ) as mock_execute:
        result = await fhir_gateway.search(
            Patient, {"name": "Smith"}, follow_pagination=True, max_pages=2
        )

        assert mock_execute.call_count == 2
        assert result.entry is not None
        assert len(result.entry) == 2
        assert [entry.resource.id for entry in result.entry] == ["1", "2"]


@pytest.mark.asyncio
async def test_search_with_pagination_empty_next_link(fhir_gateway):
    """AsyncFHIRGateway.search handles missing next links correctly."""
    bundle = Bundle(
        type="searchset",
        entry=[{"resource": Patient(id="1")}],
        link=[{"relation": "self", "url": "Patient?name=Smith"}],
    )

    with patch.object(
        fhir_gateway, "_execute_with_client", return_value=bundle
    ) as mock_execute:
        result = await fhir_gateway.search(
            Patient, {"name": "Smith"}, follow_pagination=True
        )

        mock_execute.assert_called_once()
        assert result.entry is not None
        assert len(result.entry) == 1
        assert result.entry[0].resource.id == "1"


@pytest.mark.asyncio
async def test_search_with_pagination_and_provenance(fhir_gateway):
    """AsyncFHIRGateway.search combines pagination with provenance metadata."""
    page1 = Bundle(
        type="searchset",
        entry=[{"resource": Patient(id="1")}],
        link=[{"relation": "next", "url": "Patient?page=2"}],
    )
    page2 = Bundle(type="searchset", entry=[{"resource": Patient(id="2")}])

    with patch.object(
        fhir_gateway, "_execute_with_client", side_effect=[page1, page2]
    ) as mock_execute:
        result = await fhir_gateway.search(
            Patient,
            {"name": "Smith"},
            source="test_source",
            follow_pagination=True,
            add_provenance=True,
            provenance_tag="aggregated",
        )

        assert mock_execute.call_count == 2
        assert result.entry is not None
        assert len(result.entry) == 2

        # Check provenance metadata
        for entry in result.entry:
            assert entry.resource.meta is not None
            assert entry.resource.meta.source == "urn:healthchain:source:test_source"
            assert entry.resource.meta.tag[0].code == "aggregated"


@pytest.mark.asyncio
async def test_modify_context_for_existing_resource(fhir_gateway, test_patient):
    """Modify context manager fetches, yields, and updates existing resources."""
    mock_client = AsyncMock()
    mock_client.read.return_value = test_patient
    mock_client.update.return_value = Patient(id="123", active=False)

    with patch.object(fhir_gateway, "get_client", return_value=mock_client):
        async with fhir_gateway.modify(Patient, "123") as patient:
            assert patient == test_patient
            patient.active = False

        mock_client.read.assert_called_once_with(Patient, "123")
        mock_client.update.assert_called_once_with(test_patient)


@pytest.mark.asyncio
async def test_modify_context_for_new_resource(fhir_gateway):
    """Modify context manager creates new resources when no ID provided."""
    created_patient = Patient(id="456", active=True)
    mock_client = AsyncMock()
    mock_client.create.return_value = created_patient

    with patch.object(fhir_gateway, "get_client", return_value=mock_client):
        async with fhir_gateway.modify(Patient) as patient:
            assert patient.id is None  # New resource
            patient.active = True

        mock_client.create.assert_called_once()
        # Verify the created resource was updated with returned values
        assert patient.id == "456"


@pytest.mark.asyncio
async def test_execute_with_client_handles_client_errors(fhir_gateway):
    """_execute_with_client properly handles and re-raises client errors."""
    mock_client = AsyncMock()
    mock_client.read.side_effect = Exception("Client error")

    with patch.object(fhir_gateway, "get_client", return_value=mock_client):
        with patch(
            "healthchain.gateway.fhir.errors.FHIRErrorHandler.handle_fhir_error"
        ) as mock_handler:
            mock_handler.side_effect = Exception("Handled error")

            with pytest.raises(Exception, match="Handled error"):
                await fhir_gateway._execute_with_client(
                    "read",
                    resource_type=Patient,
                    resource_id="123",
                    client_args=(Patient, "123"),
                )

            mock_handler.assert_called_once()
