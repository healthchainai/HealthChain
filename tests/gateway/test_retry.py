"""Tests for the shared retry helpers used by FHIR/OAuth2 clients."""

import asyncio

import httpx
import pytest

from healthchain.gateway.clients.retry import (
    RetryPolicy,
    async_retry_call,
    retry_call,
)


def test_retry_policy_backoff_is_exponential_and_capped():
    policy = RetryPolicy(backoff_base=1.0, backoff_factor=2.0, max_backoff=5.0)
    assert policy.delay_for(1) == 1.0
    assert policy.delay_for(2) == 2.0
    assert policy.delay_for(3) == 4.0
    assert policy.delay_for(4) == 5.0  # capped at max_backoff


def test_retry_policy_rejects_invalid_attempts():
    with pytest.raises(ValueError):
        RetryPolicy(max_attempts=0)


def test_retry_call_returns_on_first_success():
    calls = {"n": 0}

    def fn():
        calls["n"] += 1
        return "ok"

    assert retry_call(fn, RetryPolicy(max_attempts=3)) == "ok"
    assert calls["n"] == 1


def test_retry_call_retries_transient_then_succeeds(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda _s: None)
    calls = {"n": 0}

    def fn():
        calls["n"] += 1
        if calls["n"] < 3:
            raise httpx.ConnectError("boom")
        return "recovered"

    result = retry_call(fn, RetryPolicy(max_attempts=3, backoff_base=0.01))
    assert result == "recovered"
    assert calls["n"] == 3


def test_retry_call_gives_up_after_max_attempts(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda _s: None)

    def fn():
        raise httpx.ReadTimeout("slow")

    with pytest.raises(httpx.ReadTimeout):
        retry_call(fn, RetryPolicy(max_attempts=2, backoff_base=0.01))


def test_retry_call_does_not_retry_non_transient():
    calls = {"n": 0}

    def fn():
        calls["n"] += 1
        raise ValueError("permanent")

    with pytest.raises(ValueError):
        retry_call(fn, RetryPolicy(max_attempts=3))
    assert calls["n"] == 1


def test_async_retry_call_retries_transient_then_succeeds(monkeypatch):
    async def _noop(_s):
        return None

    monkeypatch.setattr("asyncio.sleep", _noop)
    calls = {"n": 0}

    async def fn():
        calls["n"] += 1
        if calls["n"] < 2:
            raise httpx.PoolTimeout("pool")
        return "async-ok"

    result = asyncio.run(
        async_retry_call(fn, RetryPolicy(max_attempts=3, backoff_base=0.01))
    )
    assert result == "async-ok"
    assert calls["n"] == 2
