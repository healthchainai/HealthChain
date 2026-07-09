import logging
import httpx

from typing import Any, Dict, Type, Union

from fhir.resources.R4B.bundle import Bundle
from fhir.resources.R4B.capabilitystatement import CapabilityStatement
from fhir.resources.resource import Resource

from healthchain.gateway.clients.auth import OAuth2TokenManager
from healthchain.gateway.clients.fhir.base import FHIRAuthConfig, FHIRServerInterface
from healthchain.gateway.clients.retry import retry_call


logger = logging.getLogger(__name__)


class FHIRClient(FHIRServerInterface):
    """
    Synchronous FHIR client optimized for HealthChain gateway use cases.

    - Uses fhir.resources for validation
    - Supports JWT Bearer token authentication
    - Synchronous with httpx
    """

    def __init__(
        self,
        auth_config: FHIRAuthConfig,
        limits: httpx.Limits = None,
        **kwargs,
    ):
        """
        Initialize the FHIR client with optional OAuth2.0 authentication.

        Supports both authenticated and public FHIR endpoints.
        Authentication is auto-detected based on auth_config.requires_auth.

        Args:
            auth_config: Authentication configuration (auth optional for public endpoints)
            limits: httpx connection limits for pooling
            **kwargs: Additional parameters passed to httpx.Client
        """
        super().__init__(auth_config)

        # Only create token manager if authentication is required
        self.token_manager = (
            OAuth2TokenManager(auth_config.to_oauth2_config())
            if auth_config.requires_auth
            else None
        )

        # Create httpx client with connection pooling and additional kwargs.
        # Fall back to the pool limits derived from auth_config when the caller
        # does not supply an explicit httpx.Limits instance.
        client_kwargs = {
            "timeout": self.timeout,
            "verify": self.verify_ssl,
            "limits": limits if limits is not None else auth_config.to_httpx_limits(),
        }

        # Pass through additional kwargs to httpx.Client
        client_kwargs.update(kwargs)

        self.client = httpx.Client(**client_kwargs)

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def _get_headers(self) -> Dict[str, str]:
        """
        Get headers with optional OAuth2.0 token.

        For authenticated endpoints, includes Authorization header.
        For public endpoints, returns base headers only.
        """
        headers = self.base_headers.copy()

        # Only add authorization header if authentication is required
        if self.token_manager is not None:
            token = self.token_manager.get_access_token()
            headers["Authorization"] = f"Bearer {token}"

        # Trace the outgoing request headers to aid debugging of auth issues
        logger.info("Prepared FHIR request headers for %s: %s", self.base_url, headers)

        return headers

    def _http_get(self, url: str, headers: Dict[str, str], **kwargs) -> httpx.Response:
        policy = self.auth_config.to_retry_policy()
        return retry_call(
            lambda: self.client.get(url, headers=headers, **kwargs), policy
        )

    def _http_post(
        self, url: str, headers: Dict[str, str], **kwargs
    ) -> httpx.Response:
        policy = self.auth_config.to_retry_policy()
        return retry_call(
            lambda: self.client.post(url, headers=headers, **kwargs), policy
        )

    def _http_put(
        self, url: str, headers: Dict[str, str], **kwargs
    ) -> httpx.Response:
        policy = self.auth_config.to_retry_policy()
        return retry_call(
            lambda: self.client.put(url, headers=headers, **kwargs), policy
        )

    def _http_patch(
        self, url: str, headers: Dict[str, str], **kwargs
    ) -> httpx.Response:
        policy = self.auth_config.to_retry_policy()
        return retry_call(
            lambda: self.client.patch(url, headers=headers, **kwargs), policy
        )

    def _http_delete(
        self, url: str, headers: Dict[str, str], **kwargs
    ) -> httpx.Response:
        policy = self.auth_config.to_retry_policy()
        return retry_call(
            lambda: self.client.delete(url, headers=headers, **kwargs), policy
        )

    def capabilities(self) -> CapabilityStatement:
        """
        Fetch the server's CapabilityStatement.

        Returns:
            CapabilityStatement resource
        """
        headers = self._get_headers()
        response = self._http_get(self._build_url("metadata"), headers=headers)
        data = self._handle_response(response)
        return CapabilityStatement(**data)

    def read(
        self, resource_type: Union[str, Type[Resource]], resource_id: str
    ) -> Resource:
        """
        Read a specific resource by ID.

        Args:
            resource_type: FHIR resource type or class
            resource_id: Resource ID

        Returns:
            Resource instance
        """
        type_name, resource_class = self._resolve_resource_type(resource_type)
        url = self._build_url(f"{type_name}/{resource_id}")
        logger.debug(f"Sending GET request to {url}")

        headers = self._get_headers()
        response = self._http_get(url, headers=headers)
        data = self._handle_response(response)

        return resource_class(**data)

    def vread(
        self,
        resource_type: Union[str, Type[Resource]],
        resource_id: str,
        version_id: str,
    ) -> Resource:
        """Read a specific version of a resource."""
        type_name, resource_class = self._resolve_resource_type(resource_type)
        url = self._build_url(f"{type_name}/{resource_id}/_history/{version_id}")
        logger.debug(f"Sending vread GET request to {url}")

        headers = self._get_headers()
        response = self._http_get(url, headers=headers)
        data = self._handle_response(response)

        return resource_class(**data)

    def history(
        self,
        resource_type: Union[str, Type[Resource]],
        resource_id: str,
        params: Dict[str, Any] = None,
    ) -> Bundle:
        """Read the version history for a resource."""
        type_name, _ = self._resolve_resource_type(resource_type)
        url = self._build_url(f"{type_name}/{resource_id}/_history", params)
        logger.debug(f"Sending history GET request to {url}")

        headers = self._get_headers()
        response = self._http_get(url, headers=headers)
        data = self._handle_response(response)

        return Bundle(**data)

    def search(
        self, resource_type: Union[str, Type[Resource]], params: Dict[str, Any] = None
    ) -> Bundle:
        """
        Search for resources.

        Args:
            resource_type: FHIR resource type or class
            params: Search parameters

        Returns:
            Bundle containing search results
        """
        type_name, _ = self._resolve_resource_type(resource_type)
        url = self._build_url(type_name, params)
        logger.debug(f"Sending GET request to {url}")

        headers = self._get_headers()
        response = self._http_get(url, headers=headers)
        data = self._handle_response(response)

        return Bundle(**data)

    def patch(
        self,
        resource_type: Union[str, Type[Resource]],
        resource_id: str,
        patch_body: list,
    ) -> Resource:
        """Apply a JSON Patch to a resource."""
        import json

        type_name, resource_class = self._resolve_resource_type(resource_type)
        url = self._build_url(f"{type_name}/{resource_id}")
        logger.debug(f"Sending PATCH request to {url}")

        headers = self._get_headers()
        headers["Content-Type"] = "application/json-patch+json"
        response = self._http_patch(
            url, headers=headers, content=json.dumps(patch_body)
        )
        data = self._handle_response(response)

        return resource_class(**data)

    def create(self, resource: Resource) -> Resource:
        """
        Create a new resource.

        Args:
            resource: Resource to create

        Returns:
            Created resource with server-assigned ID
        """
        type_name, resource_class = self._resolve_resource_type(
            resource.__resource_type__
        )
        url = self._build_url(type_name)
        logger.debug(f"Sending POST request to {url}")

        headers = self._get_headers()
        response = self._http_post(
            url, headers=headers, content=resource.model_dump_json()
        )
        data = self._handle_response(response)

        # Return the same resource type
        return resource_class(**data)

    def update(self, resource: Resource) -> Resource:
        """
        Update an existing resource.

        Args:
            resource: Resource to update (must have ID)

        Returns:
            Updated resource
        """
        if not resource.id:
            raise ValueError("Resource must have an ID for update")

        type_name, resource_class = self._resolve_resource_type(
            resource.__resource_type__
        )
        url = self._build_url(f"{type_name}/{resource.id}")
        logger.debug(f"Sending PUT request to {url}")

        headers = self._get_headers()
        response = self._http_put(
            url, headers=headers, content=resource.model_dump_json()
        )
        data = self._handle_response(response)

        # Return the same resource type
        return resource_class(**data)

    def delete(
        self, resource_type: Union[str, Type[Resource]], resource_id: str
    ) -> bool:
        """
        Delete a resource.

        Args:
            resource_type: FHIR resource type or class
            resource_id: Resource ID to delete

        Returns:
            True if successful
        """
        type_name, _ = self._resolve_resource_type(resource_type)
        url = self._build_url(f"{type_name}/{resource_id}")
        logger.debug(f"Sending DELETE request to {url}")

        headers = self._get_headers()
        response = self._http_delete(url, headers=headers)

        # Delete operations typically return 204 No Content
        if response.status_code in (200, 204):
            return True

        self._handle_response(response)  # This will raise an error
        return False

    def transaction(self, bundle: Bundle) -> Bundle:
        """
        Execute a transaction bundle.

        Args:
            bundle: Transaction bundle

        Returns:
            Response bundle
        """
        url = self._build_url("")  # Base URL for transaction
        logger.debug(f"Sending POST request to {url}")

        headers = self._get_headers()
        response = self._http_post(
            url, headers=headers, content=bundle.model_dump_json()
        )
        data = self._handle_response(response)

        return Bundle(**data)


def create_fhir_client(
    auth_config: FHIRAuthConfig,
    **additional_params,
) -> "FHIRClient":
    """
    Factory function to create and configure a sync FHIR server interface using OAuth2.0

    Args:
        auth_config: OAuth2.0 authentication configuration
        **additional_params: Additional parameters for the client

    Returns:
        A configured sync FHIRClient implementation
    """
    logger.debug(f"Creating sync FHIR server with OAuth2.0 for {auth_config.base_url}")

    return FHIRClient(auth_config=auth_config, **additional_params)
