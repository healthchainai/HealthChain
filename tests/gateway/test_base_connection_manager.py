"""
Tests for shared FHIR connection manager functionality in the HealthChain gateway system.

This module tests shared connection string validation, source management, and error handling
that should work identically across sync and async connection manager implementations.
"""

import inspect

import pytest
from unittest.mock import Mock

from healthchain.gateway.clients.fhir.base import FHIRAuthConfig
from healthchain.gateway.clients.fhir.sync.connection import FHIRConnectionManager
from healthchain.gateway.clients.fhir.aio.connection import AsyncFHIRConnectionManager
from healthchain.gateway.fhir.errors import FHIRConnectionError
from healthchain.gateway.api.protocols import FHIRServerInterfaceProtocol


@pytest.fixture(params=["sync", "async"])
def connection_manager(request):
    """Fixture providing both sync and async connection managers."""
    if request.param == "sync":
        return FHIRConnectionManager()
    else:
        return AsyncFHIRConnectionManager(
            max_connections=50, max_keepalive_connections=10, keepalive_expiry=30.0
        )


@pytest.fixture
def mock_fhir_client():
    """Create a mock FHIR client using protocol."""
    client = Mock(spec=FHIRServerInterfaceProtocol)
    client.base_url = "https://test.fhir.com/R4"
    return client


@pytest.mark.parametrize(
    "connection_string,expected_base_url",
    [
        # Valid connection strings
        (
            "fhir://epic.org/api/FHIR/R4?client_id=test&client_secret=secret&token_url=https://epic.org/token",
            "https://epic.org/api/FHIR/R4",
        ),
        (
            "fhir://localhost:8080/fhir?client_id=local&client_secret=pass&token_url=http://localhost/token",
            "https://localhost:8080/fhir",
        ),
        ("http://localhost:8080/fhir", "http://localhost:8080/fhir"),
        ("https://fhir.example.com/r4", "https://fhir.example.com/r4"),
        # Invalid connection strings
        ("ftp://not-fhir.com/api", None),  # Wrong scheme
        ("fhir://", None),  # Missing hostname
        ("invalid-string", None),  # Not a URL
    ],
)
def test_connection_manager_source_validation_and_parsing(
    connection_manager, connection_string, expected_base_url
):
    """Connection managers parse connection strings once and store the config."""
    if expected_base_url:
        connection_manager.add_source("test_source", connection_string)
        config = connection_manager.sources["test_source"]
        assert isinstance(config, FHIRAuthConfig)
        assert config.base_url == expected_base_url
    else:
        with pytest.raises(
            FHIRConnectionError, match="Failed to parse connection string"
        ):
            connection_manager.add_source("test_source", connection_string)


@pytest.mark.asyncio
async def test_connection_manager_handles_invalid_source_gracefully(connection_manager):
    """Connection managers handle requests for unknown sources gracefully."""
    # Add one valid source
    connection_manager.add_source(
        "valid_source",
        "fhir://valid.com/fhir?client_id=test&client_secret=secret&token_url=https://valid.com/token",
    )

    # Request client for non-existent source - should raise ValueError
    with pytest.raises(ValueError, match="Unknown source: invalid_source"):
        if hasattr(connection_manager, "get_client"):
            # Check if it's async by seeing if the method is a coroutine function
            if inspect.iscoroutinefunction(connection_manager.get_client):
                # For async version
                await connection_manager.get_client("invalid_source")
            else:
                # For sync version
                connection_manager.get_client("invalid_source")

    # Verify the source was actually added correctly
    assert "valid_source" in connection_manager.sources


@pytest.mark.asyncio
async def test_connection_manager_handles_duplicate_source_names(connection_manager):
    """Connection managers overwrite duplicate source names and serve the new config."""
    original_connection = "fhir://same.com/fhir?client_id=test&client_secret=old&token_url=https://same.com/token"
    updated_connection = "fhir://same.com/fhir?client_id=test&client_secret=new&token_url=https://same.com/token"
    connection_manager._create_client = Mock(side_effect=lambda *a, **k: Mock())

    async def get_client():
        if inspect.iscoroutinefunction(connection_manager.get_client):
            return await connection_manager.get_client("duplicate_source")
        return connection_manager.get_client("duplicate_source")

    connection_manager.add_source("duplicate_source", original_connection)
    first = await get_client()
    second = await get_client()
    assert (
        connection_manager.sources["duplicate_source"].client_secret.get_secret_value()
        == "old"
    )

    # Same endpoint, new credentials
    connection_manager.add_source("duplicate_source", updated_connection)
    replaced = await get_client()
    assert (
        connection_manager.sources["duplicate_source"].client_secret.get_secret_value()
        == "new"
    )
    created_config = connection_manager._create_client.call_args[0][0]
    assert created_config.client_secret.get_secret_value() == "new"
    assert replaced is not first

    # Secret rotated in place
    connection_manager.sources["duplicate_source"].client_secret = "newer"
    rotated = await get_client()
    assert rotated is not replaced

    # Async pools the client per config; sync builds a fresh one per call
    if isinstance(connection_manager, AsyncFHIRConnectionManager):
        assert second is first

    # Should only have one source with that name
    assert list(connection_manager.sources.keys()) == ["duplicate_source"]


def test_connection_manager_initialization_state(connection_manager):
    """Connection managers initialize with empty state."""
    assert len(connection_manager.sources) == 0
    assert isinstance(connection_manager.sources, dict)


def test_connection_manager_source_name_validation(connection_manager):
    """Connection managers accept various source name formats."""
    valid_names = [
        "simple_name",
        "name-with-dashes",
        "name.with.dots",
        "name_123",
        "UPPERCASE_NAME",
        "MixedCase_Name-123.test",
    ]

    connection_string = "fhir://test.com/fhir?client_id=test&client_secret=secret&token_url=https://test.com/token"

    for name in valid_names:
        connection_manager.add_source(name, connection_string)
        assert name in connection_manager.sources
