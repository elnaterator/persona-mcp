"""Integration tests for the Postgres-backed OAuth-proxy key-value store."""

import asyncio
from collections.abc import Coroutine
from typing import Any, TypeVar

import pytest
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from persona.oauth_store import PostgresKVStore, build_oauth_client_storage

T = TypeVar("T")


def _run(coro: Coroutine[Any, Any, T]) -> T:
    return asyncio.run(coro)


@pytest.fixture
def kv_pool(_schema_applied, pg_dsn: str):
    """A real connection pool against the test Postgres, cleaned up per test.

    The store commits its own short transactions (unlike the rolled-back
    ``db_conn`` fixture), so rows are purged on teardown to isolate tests.
    """
    pool = ConnectionPool(
        pg_dsn, min_size=1, max_size=2, open=True, kwargs={"row_factory": dict_row}
    )
    try:
        yield pool
    finally:
        with pool.connection() as conn:
            conn.execute("DELETE FROM oauth_kv")
        pool.close()


class TestPostgresKVStore:
    def test_put_get_roundtrip(self, kv_pool: ConnectionPool[Any]) -> None:
        store = PostgresKVStore(kv_pool)

        async def scenario() -> dict[str, Any] | None:
            await store.put("k1", {"a": 1, "b": "x"}, collection="c1")
            return await store.get("k1", collection="c1")

        assert _run(scenario()) == {"a": 1, "b": "x"}

    def test_put_overwrites(self, kv_pool: ConnectionPool[Any]) -> None:
        store = PostgresKVStore(kv_pool)

        async def scenario() -> dict[str, Any] | None:
            await store.put("k1", {"v": 1}, collection="c1")
            await store.put("k1", {"v": 2}, collection="c1")
            return await store.get("k1", collection="c1")

        assert _run(scenario()) == {"v": 2}

    def test_delete(self, kv_pool: ConnectionPool[Any]) -> None:
        store = PostgresKVStore(kv_pool)

        async def scenario() -> tuple[bool, dict[str, Any] | None]:
            await store.put("k1", {"a": 1}, collection="c1")
            deleted = await store.delete("k1", collection="c1")
            return deleted, await store.get("k1", collection="c1")

        deleted, after = _run(scenario())
        assert deleted is True
        assert after is None

    def test_missing_key_returns_none(self, kv_pool: ConnectionPool[Any]) -> None:
        store = PostgresKVStore(kv_pool)
        assert _run(store.get("nope", collection="c1")) is None

    def test_expired_entry_not_returned(self, kv_pool: ConnectionPool[Any]) -> None:
        store = PostgresKVStore(kv_pool)

        async def scenario() -> dict[str, Any] | None:
            await store.put("k1", {"a": 1}, collection="c1", ttl=0.01)
            await asyncio.sleep(0.05)
            return await store.get("k1", collection="c1")

        assert _run(scenario()) is None

    def test_collections_isolated(self, kv_pool: ConnectionPool[Any]) -> None:
        store = PostgresKVStore(kv_pool)

        async def scenario() -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
            await store.put("k", {"v": "c1"}, collection="c1")
            await store.put("k", {"v": "c2"}, collection="c2")
            return (
                await store.get("k", collection="c1"),
                await store.get("k", collection="c2"),
            )

        a, b = _run(scenario())
        assert a == {"v": "c1"}
        assert b == {"v": "c2"}


class TestEncryptedClientStorage:
    def test_roundtrip_through_encryption_wrapper(
        self, kv_pool: ConnectionPool[Any]
    ) -> None:
        store = build_oauth_client_storage(kv_pool, "clerk-secret-value")

        async def scenario() -> dict[str, Any] | None:
            await store.put(
                "k", {"token": "sensitive"}, collection="mcp-upstream-tokens"
            )
            return await store.get("k", collection="mcp-upstream-tokens")

        assert _run(scenario()) == {"token": "sensitive"}

    def test_value_is_ciphertext_at_rest(self, kv_pool: ConnectionPool[Any]) -> None:
        store = build_oauth_client_storage(kv_pool, "clerk-secret-value")

        async def scenario() -> None:
            await store.put("k", {"token": "sensitive-plaintext"}, collection="col")

        _run(scenario())

        with kv_pool.connection() as conn:
            rows = conn.execute("SELECT value FROM oauth_kv").fetchall()
        assert rows, "expected at least one stored row"
        assert all("sensitive-plaintext" not in row["value"] for row in rows)
