import atexit
import sqlite3


def _normalize_isin(isin: str) -> str:
    return isin.strip()


def _normalize_title(title: str) -> str:
    return title.strip()


class ISINRegistry:
    REG_FILE_ABSPATH = __file__.removesuffix(".py") + ".sqlite3"
    _connection: sqlite3.Connection = sqlite3.connect(REG_FILE_ABSPATH)

    @classmethod
    def _ensure_reg_exists(cls) -> None:
        # The primary key gives ISIN uniqueness and an index for lookups.
        cls._connection.execute(
            "CREATE TABLE IF NOT EXISTS isin_registry ("
            "isin TEXT NOT NULL PRIMARY KEY, "
            "title TEXT NOT NULL"
            ")"
        )
        cls._connection.commit()

    @classmethod
    def add_isin_title(cls, isin: str, title: str) -> None:
        # The context commits the write without closing the connection.
        with cls._connection:
            cls._connection.execute(
                "INSERT OR IGNORE INTO isin_registry (isin, title) VALUES (?, ?)",
                (_normalize_isin(isin), _normalize_title(title)),
            )

    @classmethod
    def upd_isin_title(cls, isin: str, title: str) -> None:
        with cls._connection:
            # excluded.title is the new value from the attempted insertion.
            cls._connection.execute(
                "INSERT INTO isin_registry (isin, title) VALUES (?, ?) "
                "ON CONFLICT(isin) DO UPDATE SET title = excluded.title",
                (_normalize_isin(isin), _normalize_title(title)),
            )

    @classmethod
    def get_isin_title(cls, isin: str) -> str | None:
        row = cls._connection.execute(
            "SELECT title FROM isin_registry WHERE isin = ?",
            (_normalize_isin(isin),),
        ).fetchone()
        return row[0] if row is not None else None

    @classmethod
    def del_isin(cls, isin: str) -> int:
        with cls._connection:
            cursor = cls._connection.execute(
                "DELETE FROM isin_registry WHERE isin = ?",
                (_normalize_isin(isin),),
            )
        return cursor.rowcount


ISINRegistry._ensure_reg_exists()
atexit.register(ISINRegistry._connection.close)
