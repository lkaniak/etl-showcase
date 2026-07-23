from contextlib import asynccontextmanager
from pathlib import Path

import aiosqlite


class SqliteConnection:
    def __init__(self, conn: aiosqlite.Connection):
        self._conn = conn

    @asynccontextmanager
    async def transaction(self):
        await self._conn.execute("BEGIN")
        try:
            yield
            await self._conn.commit()
        except Exception:
            await self._conn.rollback()
            raise

    async def execute(self, query: str, params: tuple):
        await self._conn.execute(query, params)


class _AcquireContext:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._conn: aiosqlite.Connection | None = None

    async def __aenter__(self) -> SqliteConnection:
        self._conn = await aiosqlite.connect(self.db_path)
        return SqliteConnection(self._conn)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._conn is not None:
            await self._conn.close()


class SqliteConnectionPool:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def acquire(self):
        return _AcquireContext(self.db_path)


def get_sqlite_connection_pool(db_path: Path) -> SqliteConnectionPool:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return SqliteConnectionPool(db_path)
