"""PostgreSQL-backed key-value store for FastMCP OAuth-proxy state.

FastMCP's ``OAuthProxy`` persists its state (DCR client registrations, encrypted
upstream Clerk tokens, JTI→token mappings, in-flight authorize transactions and
one-time codes) through an ``AsyncKeyValue`` handle. The library default is a
local ``DiskStore``, which is fine for a long-running container but wrong for a
serverless deploy: Lambda's filesystem is read-only outside ``/tmp``, and ``/tmp``
is per-execution-environment and ephemeral — the OAuth flow spans several requests
that may land on different instances, and issued reference tokens must survive cold
starts. This store puts that state in the app's existing PostgreSQL database instead,
so it is shared across instances and durable.

Values are still encrypted at rest: ``build_oauth_client_storage`` wraps this store
in FastMCP's ``FernetEncryptionWrapper`` (see ``auth.build_mcp_auth``), so only
ciphertext reaches the ``value`` column. The ``expires_at`` metadata stays in the
clear so expired rows can be culled.
"""

import asyncio
import base64
import hashlib
from datetime import datetime
from typing import Any

from cryptography.fernet import Fernet
from key_value.aio.stores.base import BaseStore
from key_value.aio.wrappers.encryption import FernetEncryptionWrapper
from key_value.shared.utils.managed_entry import ManagedEntry
from psycopg_pool import ConnectionPool


class PostgresKVStore(BaseStore):
    """``AsyncKeyValue`` store backed by the shared application PostgreSQL pool.

    Rows live in the ``oauth_kv`` table (created by migration v12→v13), keyed by
    ``(collection, key)``. ``BaseStore`` implements the whole protocol surface
    (get/put/delete plus batch and TTL variants) on top of the three managed-entry
    methods below; expiry is enforced by ``BaseStore`` on read via
    ``ManagedEntry.is_expired``, and stale rows are culled once per process on setup.
    """

    def __init__(
        self, pool: ConnectionPool[Any], *, default_collection: str | None = None
    ) -> None:
        self._pool = pool
        # stable_api=True: our on-disk format is just the library's own JSON
        # serialization, so there is no additional stability caveat to warn about.
        super().__init__(default_collection=default_collection, stable_api=True)

    async def _setup(self) -> None:
        # The table is provisioned by the schema migration, not by the store, so
        # a read-only replica never issues DDL. Cull expired rows once per process
        # to bound growth (transient codes/transactions are also deleted inline by
        # the proxy after use).
        await asyncio.to_thread(self._db_cull_expired)

    async def _get_managed_entry(
        self, *, collection: str, key: str
    ) -> ManagedEntry | None:
        payload = await asyncio.to_thread(self._db_get, collection, key)
        if payload is None:
            return None
        return self._serialization_adapter.load_json(json_str=payload)

    async def _put_managed_entry(
        self, *, collection: str, key: str, managed_entry: ManagedEntry
    ) -> None:
        payload = self._serialization_adapter.dump_json(
            entry=managed_entry, key=key, collection=collection
        )
        await asyncio.to_thread(
            self._db_put, collection, key, payload, managed_entry.expires_at
        )

    async def _delete_managed_entry(self, *, collection: str, key: str) -> bool:
        return await asyncio.to_thread(self._db_delete, collection, key)

    # -- sync DB helpers, run off the event loop via asyncio.to_thread --

    def _db_get(self, collection: str, key: str) -> str | None:
        with self._pool.connection() as conn:
            row = conn.execute(
                "SELECT value FROM oauth_kv WHERE collection = %s AND key = %s",
                (collection, key),
            ).fetchone()
        if row is None:
            return None
        return row["value"] if isinstance(row, dict) else row[0]

    def _db_put(
        self, collection: str, key: str, value: str, expires_at: datetime | None
    ) -> None:
        with self._pool.connection() as conn:
            conn.execute(
                "INSERT INTO oauth_kv (collection, key, value, expires_at) "
                "VALUES (%s, %s, %s, %s) "
                "ON CONFLICT (collection, key) DO UPDATE SET "
                "value = EXCLUDED.value, expires_at = EXCLUDED.expires_at",
                (collection, key, value, expires_at),
            )

    def _db_delete(self, collection: str, key: str) -> bool:
        with self._pool.connection() as conn:
            cur = conn.execute(
                "DELETE FROM oauth_kv WHERE collection = %s AND key = %s",
                (collection, key),
            )
            return cur.rowcount > 0

    def _db_cull_expired(self) -> None:
        with self._pool.connection() as conn:
            conn.execute(
                "DELETE FROM oauth_kv "
                "WHERE expires_at IS NOT NULL AND expires_at < now()"
            )


def _derive_fernet_key(secret: str) -> bytes:
    """Derive a stable Fernet key from a long-lived secret.

    The same secret yields the same key on every instance, so ciphertext written
    by one Lambda invocation is readable by the next. Fernet requires a urlsafe
    base64-encoded 32-byte key.
    """
    digest = hashlib.sha256(f"persona-oauth-kv:{secret}".encode()).digest()
    return base64.urlsafe_b64encode(digest)


def build_oauth_client_storage(
    pool: ConnectionPool[Any], encryption_secret: str
) -> FernetEncryptionWrapper:
    """Build the encrypted, Postgres-backed client storage for the OAuth proxy.

    Passing ``client_storage`` to ``OAuthProxy`` disables the library's own
    encryption wrapper, so we apply Fernet encryption here to keep upstream Clerk
    tokens encrypted at rest.
    """
    return FernetEncryptionWrapper(
        key_value=PostgresKVStore(pool),
        fernet=Fernet(key=_derive_fernet_key(encryption_secret)),
    )
