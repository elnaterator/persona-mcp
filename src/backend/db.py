"""Database connection protocol based on PEP 249 DB-API 2.0."""

from typing import Any, Protocol


class DBConnection(Protocol):
    """Abstract database connection type.

    Captures the PEP 249 DB-API 2.0 methods used by the application.
    Both sqlite3.Connection and psycopg connections satisfy this protocol.
    """

    def execute(self, sql: str, parameters: Any = ..., /) -> Any: ...

    def cursor(self) -> Any: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...

    def close(self) -> None: ...
