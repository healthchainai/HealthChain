import logging

from typing import Dict

from healthchain.gateway.clients.fhir.base import (
    FHIRAuthConfig,
    FHIRServerInterface,
    parse_fhir_auth_connection_string,
)
from healthchain.gateway.fhir.errors import FHIRConnectionError


logger = logging.getLogger(__name__)


class FHIRConnectionManager:
    """
    Base FHIR connection manager for sync clients.

    Handles connection strings, source configuration, and provides
    sync FHIR clients.
    """

    def __init__(self):
        """Initialize the sync connection manager."""
        # Source name -> FHIRAuthConfig
        self.sources = {}

    def add_source(self, name: str, connection_string: str | FHIRAuthConfig) -> None:
        """
        Add a FHIR data source using a connection string or a FHIRAuthConfig.

        A connection string is parsed once here; the resulting config is stored.

        Format: fhir://hostname:port/path?param1=value1&param2=value2
        (fhir:// resolves to https; http:// and https:// are kept as given)

        Examples:
            fhir://epic.org/api/FHIR/R4?client_id=my_app&client_secret=secret&token_url=https://epic.org/oauth2/token&use_jwt_assertion=true
            fhir://cerner.org/r4?client_id=app_id&client_secret=app_secret&token_url=https://cerner.org/token&scope=openid

        Args:
            name: Source name identifier
            connection_string: FHIR connection string, or a FHIRAuthConfig

        Raises:
            FHIRConnectionError: If connection string is invalid
        """
        try:
            if isinstance(connection_string, FHIRAuthConfig):
                auth_config = connection_string
            else:
                auth_config = parse_fhir_auth_connection_string(connection_string)
        except ValueError as e:
            raise FHIRConnectionError(
                message=f"Failed to parse connection string: {str(e)}",
                code="Invalid connection string",
                state="500",
            )

        self.sources[name] = auth_config
        logger.info(f"Added FHIR source '{name}'")

    def get_client(self, source: str = None) -> FHIRServerInterface:
        """
        Get a sync FHIR client for the specified source.

        Args:
            source: Source name to get client for (uses first available if None)

        Returns:
            FHIRServerInterface: A sync FHIR client

        Raises:
            ValueError: If source is unknown or has no connection config
        """
        return self._create_client(self._get_auth_config(source))

    def get_status(self) -> Dict[str, any]:
        """
        Get the current status of the sync connection manager.

        Returns:
            Dict containing status information for sync clients.
        """
        return {
            "client_type": "sync",
            "pooling_enabled": False,
            "sources": {
                "count": len(self.sources),
                "configured": list(self.sources.keys()),
            },
        }

    def get_sources(self) -> Dict[str, any]:
        """
        Get all configured sources.

        Returns:
            Dict of source names and their configurations
        """
        return self.sources.copy()

    def _get_auth_config(self, source: str = None) -> FHIRAuthConfig:
        """Look up the stored config for a source (first source if None)."""
        source_name = source or next(iter(self.sources.keys()))
        if source_name not in self.sources:
            raise ValueError(f"Unknown source: {source_name}")

        auth_config = self.sources[source_name]
        if not isinstance(auth_config, FHIRAuthConfig):
            raise ValueError(f"No connection config found for source: {source_name}")
        return auth_config

    def _create_client(self, auth_config: FHIRAuthConfig) -> FHIRServerInterface:
        """
        Create a sync FHIR server instance from a stored config.

        Args:
            auth_config: FHIR connection and auth configuration

        Returns:
            FHIRServerInterface: A new sync FHIR server instance
        """
        from healthchain.gateway.clients.fhir.sync.client import create_fhir_client

        return create_fhir_client(auth_config=auth_config)
