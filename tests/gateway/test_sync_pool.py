"""Tests for sync FHIR connection pooling."""

from unittest.mock import patch

import pytest

from healthchain.gateway.clients.fhir.sync.connection import FHIRConnectionManager
from healthchain.gateway.clients.pool import SyncClientPool


VALID_CONN = (
    "fhir://example.com/fhir/R4?"
    "client_id=test&client_secret=secret&token_url=https://example.com/token"
)


def test_sync_client_pool_reuses_clients():
    pool = SyncClientPool()
    created = []

    def factory(conn_str, limits=None):
        created.append(conn_str)
        return {"conn": conn_str, "limits": limits}

    c1 = pool.get_client("fhir://a", factory)
    c2 = pool.get_client("fhir://a", factory)
    c3 = pool.get_client("fhir://b", factory)

    assert c1 is c2
    assert c1 is not c3
    assert len(created) == 2


def test_sync_client_pool_close_all():
    pool = SyncClientPool()
    closed = []

    class FakeClient:
        def close(self):
            closed.append(True)

    pool._clients["x"] = FakeClient()
    pool.close_all()
    assert len(closed) == 1
    assert pool.get_pool_stats()["total_clients"] == 0


def test_sync_connection_manager_pools_clients():
    mgr = FHIRConnectionManager()
    mgr.add_source("epic", VALID_CONN)

    with patch.object(mgr, "_create_server_from_connection_string") as mock_create:
        mock_create.return_value = object()
        c1 = mgr.get_client("epic")
        c2 = mgr.get_client("epic")
        assert c1 is c2
        assert mock_create.call_count == 1


def test_sync_connection_manager_status_reports_pooling():
    mgr = FHIRConnectionManager()
    mgr.add_source("epic", VALID_CONN)
    status = mgr.get_status()
    assert status["pooling_enabled"] is True
    assert "pool_stats" in status
    assert "epic" in status["sources"]["configured"]
