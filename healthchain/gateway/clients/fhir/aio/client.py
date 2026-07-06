import logging
import httpx

from typing import Any, Dict, Type, Union

from fhir.resources.R4B.bundle import Bundle
from fhir.resources.R4B.capabilitystatement import CapabilityStatement
from fhir.resources.resource import Resource

from healthchain.gateway.clients.auth import AsyncOAuth2TokenManager
from healthchain.gateway.clients.fhir.base import FHIRAuthConfig, FHIRServerInterface
from healthchain.gateway.clients.retry import async_retry_call


logger = logging.getLogger(__name__)


class AsyncFHIRClient(FHIRServerInterface):
    """
    Async FHIR client optimized for HealthChain gateway use cases.

    - Uses fhir.resources for validation
    - Supports JWT Bearer token authentication
    - Async-first with httpx
    """

    def __init__(
        self,
        auth_config: FHIRAuthConfig,
        limits: httpx.Limits = None,
        **kwargs,
    ):
        """
        Initialize the FHIR client with OAuth2.0 authentication.

        Args:
            auth_config: OAuth2.0 authentication configuration
            limits: httpx connection limits for pooling
            **kwargs: Additional parameters passed to httpx.AsyncClient
        """
        super().__init__(auth_config)
        self.token_manager = AsyncOAuth2TokenManager(auth_config.to_oauth2_config())

        # Create httpx client with connection pooling and additional kwargs.
        # Fall back to the pool limits derived from auth_config when the caller
        # does not supply an explicit httpx.Limits instance.
        client_kwargs = {
            "timeout": self.timeout,
            "verify": self.verify_ssl,
            "limits": limits if limits is not None else auth_config.to_httpx_limits(),
        }

        # Pass through additional kwargs to httpx.AsyncClient
        client_kwargs.update(kwargs)

        self.client = httpx.AsyncClient(**client_kwargs)

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def _get_headers(self) -> Dict[str, str]:
        """Get headers with fresh OAuth2.0 token."""
        headers = self.base_headers.copy()
        token = await self.token_manager.get_access_token()
        headers["Authorization"] = f"Bearer {token}"

        return headers

    async def _http_get(self, url: str, headers: Dict[str, str], **kwargs) -> httpx.Response:
        policy = self.auth_config.to_retry_policy()

        async def _do():
            return await self.client.get(url, headers=headers, **kwargs)

        return await async_retry_call(_do, policy)

    async def _http_post(
        self, url: str, headers: Dict[str, str], **kwargs
    ) -> httpx.Response:
        policy = self.auth_config.to_retry_policy()

        async def _do():
            return await self.client.post(url, headers=headers, **kwargs)

        return await async_retry_call(_do, policy)

    async def _http_put(
        self, url: str, headers: Dict[str, str], **kwargs
    ) -> httpx.Response:
        policy = self.auth_config.to_retry_policy()

        async def _do():
            return await self.client.put(url, headers=headers, **kwargs)

        return await async_retry_call(_do, policy)

    async def _http_patch(
        self, url: str, headers: Dict[str, str], **kwargs
    ) -> httpx.Response:
        policy = self.auth_config.to_retry_policy()

        async def _do():
            return await self.client.patch(url, headers=headers, **kwargs)

        return await async_retry_call(_do, policy)

    async def _http_delete(
        self, url: str, headers: Dict[str, str], **kwargs
    ) -> httpx.Response:
        policy = self.auth_config.to_retry_policy()

        async def _do():
            return await self.client.delete(url, headers=headers, **kwargs)

        return await async_retry_call(_do, policy)

    async def capabilities(self) -> CapabilityStatement:
        """
        Fetch the server's CapabilityStatement.

        Returns:
            CapabilityStatement resource
        """
        headers = await self._get_headers()
        response = await self._http_get(self._build_url("metadata"), headers=headers)
        data = self._handle_response(response)
        return CapabilityStatement(**data)

    async def read(
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

        headers = await self._get_headers()
        response = await self._http_get(url, headers=headers)
        data = self._handle_response(response)

        return resource_class(**data)

    async def vread(
        self,
        resource_type: Union[str, Type[Resource]],
        resource_id: str,
        version_id: str,
    ) -> Resource:
        """Read a specific version of a resource."""
        type_name, resource_class = self._resolve_resource_type(resource_type)
        url = self._build_url(f"{type_name}/{resource_id}/_history/{version_id}")
        logger.debug(f"Sending vread GET request to {url}")

        headers = await self._get_headers()
        response = await self._http_get(url, headers=headers)
        data = self._handle_response(response)

        return resource_class(**data)

    async def history(
        self,
        resource_type: Union[str, Type[Resource]],
        resource_id: str,
        params: Dict[str, Any] = None,
    ) -> Bundle:
        """Read the version history for a resource."""
        type_name, _ = self._resolve_resource_type(resource_type)
        url = self._build_url(f"{type_name}/{resource_id}/_history", params)
        logger.debug(f"Sending history GET request to {url}")

        headers = await self._get_headers()
        response = await self._http_get(url, headers=headers)
        data = self._handle_response(response)

        return Bundle(**data)

    async def search(
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

        headers = await self._get_headers()
        response = await self._http_get(url, headers=headers)
        data = self._handle_response(response)

        return Bundle(**data)

    async def patch(
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

        headers = await self._get_headers()
        headers["Content-Type"] = "application/json-patch+json"
        response = await self._http_patch(
            url, headers=headers, content=json.dumps(patch_body)
        )
        data = self._handle_response(response)

        return resource_class(**data)

    async def create(self, resource: Resource) -> Resource:
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

        headers = await self._get_headers()
        response = await self._http_post(
            url, headers=headers, content=resource.model_dump_json()
        )
        data = self._handle_response(response)

        # Return the same resource type
        return resource_class(**data)

    async def update(self, resource: Resource) -> Resource:
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

        headers = await self._get_headers()
        response = await self._http_put(
            url, headers=headers, content=resource.model_dump_json()
        )
        data = self._handle_response(response)

        # Return the same resource type
        return resource_class(**data)

    async def delete(
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

        headers = await self._get_headers()
        response = await self._http_delete(url, headers=headers)

        # Delete operations typically return 204 No Content
        if response.status_code in (200, 204):
            return True

        self._handle_response(response)  # This will raise an error
        return False

    async def transaction(self, bundle: Bundle) -> Bundle:
        """
        Execute a transaction bundle.

        Args:
            bundle: Transaction bundle

        Returns:
            Response bundle
        """
        url = self._build_url("")  # Base URL for transaction
        logger.debug(f"Sending POST request to {url}")

        headers = await self._get_headers()
        response = await self._http_post(
            url, headers=headers, content=bundle.model_dump_json()
        )
        data = self._handle_response(response)

        return Bundle(**data)


def create_async_fhir_client(
    auth_config: FHIRAuthConfig,
    limits: httpx.Limits = None,
    **additional_params,
) -> AsyncFHIRClient:
    """
    Factory function to create and configure an async FHIR server interface using OAuth2.0

    Args:
        auth_config: OAuth2.0 authentication configuration
        limits: httpx connection limits for pooling
        **additional_params: Additional parameters for the client

    Returns:
        A configured async AsyncFHIRClient implementation
    """
    logger.debug(f"Creating async FHIR server with OAuth2.0 for {auth_config.base_url}")

    return AsyncFHIRClient(auth_config=auth_config, limits=limits, **additional_params)
