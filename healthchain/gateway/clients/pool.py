import httpx

from typing import Any, Callable, Dict, Generic, Hashable, TypeVar

# Generic client interface type
ClientInterface = TypeVar("ClientInterface")


class ClientPool(Generic[ClientInterface]):
    """
    Generic client pool for managing client instances with connection pooling using httpx.
    Handles connection lifecycle, timeouts, and resource cleanup for any client type.
    """

    def __init__(
        self,
        max_connections: int = 100,
        max_keepalive_connections: int = 20,
        keepalive_expiry: float = 5.0,
    ):
        """
        Initialize the client pool.

        Args:
            max_connections: Maximum number of total connections
            max_keepalive_connections: Maximum number of keep-alive connections
            keepalive_expiry: How long to keep connections alive (seconds)
        """
        self._clients: Dict[Hashable, ClientInterface] = {}
        self._client_limits = httpx.Limits(
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections,
            keepalive_expiry=keepalive_expiry,
        )

    async def get_client(
        self, connection_string: Hashable, client_factory: Callable
    ) -> ClientInterface:
        """
        Get a client for the given connection string.

        Args:
            connection_string: Key identifying the client's configuration
            client_factory: Factory function to create new clients

        Returns:
            ClientInterface: A client with pooled connections
        """
        if connection_string not in self._clients:
            # Create new client with connection pooling
            self._clients[connection_string] = client_factory(
                connection_string, limits=self._client_limits
            )

        return self._clients[connection_string]

    async def close_all(self):
        """Close all client connections."""
        for client in self._clients.values():
            if hasattr(client, "close"):
                await client.close()
        self._clients.clear()

    def get_pool_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics."""
        stats = {
            "total_clients": len(self._clients),
            "limits": {
                "max_connections": self._client_limits.max_connections,
                "max_keepalive_connections": self._client_limits.max_keepalive_connections,
                "keepalive_expiry": self._client_limits.keepalive_expiry,
            },
            # A list, so pool keys (which may hold credentials) are never exposed
            "clients": [],
        }

        for client in self._clients.values():
            # httpx clients keep their httpcore pool on the default transport;
            # custom transports (e.g. httpx.MockTransport) have no pool
            client_stats = {}
            transport = getattr(getattr(client, "client", None), "_transport", None)
            pool = getattr(transport, "_pool", None)
            if pool is not None:
                connections = pool.connections
                client_stats.update(
                    {
                        "active_connections": len(connections),
                        "available_connections": sum(
                            c.is_available() for c in connections
                        ),
                    }
                )
            stats["clients"].append(client_stats)

        return stats
