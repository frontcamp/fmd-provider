import atexit
import sqlite3
from typing import ClassVar

_APP_NAME = 'isinreg'
_APP_VERSION = '0.1.0'
_APP_TITLE = 'ISIN Registry'
_APP_COPYRIGHT = 'Copyright (C) 2026 Maksym Plaksin'

_APP_INTRO = f'''{_APP_NAME} {_APP_VERSION}
{_APP_TITLE}
{_APP_COPYRIGHT}'''


def _normalize_isin(isin: str) -> str:
    return isin.strip()

def _normalize_title(title: str) -> str:
    return title.strip()

def _normalize_short(short: str) -> str:
    return short.strip()


class ISINRegistry:
    REG_FILE_ABSPATH = __file__.removesuffix(".py") + ".sqlite3"
    _connection: sqlite3.Connection = sqlite3.connect(REG_FILE_ABSPATH)
    _updcache: ClassVar[list[tuple[str, str, str]]] = []

    @classmethod
    def _ensure_reg_exists(cls) -> None:
        # The primary key gives ISIN uniqueness and an index for lookups.
        cls._connection.execute(
            "CREATE TABLE IF NOT EXISTS isin_registry ("
            "  isin TEXT NOT NULL PRIMARY KEY, "
            "  title TEXT NOT NULL, "
            "  short TEXT NOT NULL"
            ")"
        )
        cls._connection.commit()

    @classmethod
    def add_isin_info(cls, isin: str, title: str, short: str) -> None:
        # The context commits the write without closing the connection.
        with cls._connection:
            cls._connection.execute(
                "INSERT OR IGNORE "
                "  INTO isin_registry (isin, title, short) "
                "  VALUES (?, ?, ?)",
                (_normalize_isin(isin),
                 _normalize_title(title),
                 _normalize_short(short)),
            )

    @classmethod
    def upd_isin_info(cls, isin: str, title: str, short: str) -> None:
        with cls._connection:
            # excluded holds the new values from the attempted insertion.
            cls._connection.execute(
                "INSERT "
                "  INTO isin_registry (isin, title, short) "
                "  VALUES (?, ?, ?) "
                "  ON CONFLICT(isin) "
                "    DO UPDATE "
                "      SET "
                "        title = excluded.title, "
                "        short = excluded.short",
                (_normalize_isin(isin),
                 _normalize_title(title),
                 _normalize_short(short)),
            )

    @classmethod
    def get_isin_title(cls, isin: str, fallback_to_isin: bool = False) -> str | None:
        normalized_isin = _normalize_isin(isin)
        row = cls._connection.execute(
            "SELECT title FROM isin_registry WHERE isin = ?",
            (normalized_isin,),
        ).fetchone()
        result = row[0] if row is not None else None
        if fallback_to_isin and (result is None or result == ""):
            return normalized_isin
        return result

    @classmethod
    def get_isin_short(cls, isin: str, fallback_to_isin: bool = False) -> str | None:
        normalized_isin = _normalize_isin(isin)
        row = cls._connection.execute(
            "SELECT short FROM isin_registry WHERE isin = ?",
            (normalized_isin,),
        ).fetchone()
        result = row[0] if row is not None else None
        if fallback_to_isin and (result is None or result == ""):
            return normalized_isin
        return result

    @classmethod
    def get_isins(cls) -> list[str]:
        return [row[0] for row in cls._connection.execute(
            "SELECT isin FROM isin_registry"
        )]

    @classmethod
    def del_isin(cls, isin: str) -> int:
        with cls._connection:
            cursor = cls._connection.execute(
                "DELETE FROM isin_registry WHERE isin = ?",
                (_normalize_isin(isin),),
            )
        return cursor.rowcount

    @classmethod
    def del_isins(cls, isins: list[str]) -> None:
        with cls._connection:
            cls._connection.executemany(
                "DELETE FROM isin_registry WHERE isin = ?",
                ((_normalize_isin(isin),) for isin in isins),
            )
        cls._connection.execute("VACUUM")

    @classmethod
    def upsert_isin_info_batch(cls, isin: str, title: str, short: str) -> bool:
        # Queue a normalized record; an empty ISIN requests a final flush.
        normalized_isin = _normalize_isin(isin)
        if normalized_isin:
            cls._updcache.append(
                (normalized_isin, _normalize_title(title), _normalize_short(short))
            )

        # An empty cache has nothing to write.
        if not cls._updcache:
            return False

        # Keep a partial batch unless an empty ISIN requested its flush.
        if normalized_isin and len(cls._updcache) < 5000:
            return False

        # Commit the batch, then clear only the successfully written records.
        with cls._connection:
            cls._connection.executemany(
                "INSERT "
                "  INTO isin_registry (isin, title, short) "
                "  VALUES (?, ?, ?) "
                "  ON CONFLICT(isin) "
                "    DO UPDATE "
                "      SET "
                "        title = excluded.title, "
                "        short = excluded.short",
                cls._updcache,
            )
        cls._updcache.clear()
        return True


ISINRegistry._ensure_reg_exists()
atexit.register(ISINRegistry._connection.close)


if __name__ == "__main__":
    with open(ISINRegistry.REG_FILE_ABSPATH, "rb") as reg_file_obj:
        reg_file_obj.seek(0, 2)
        file_size = reg_file_obj.tell()

    total, empty_title, empty_short = ISINRegistry._connection.execute(
        "SELECT COUNT(*), "
        "COUNT(*) FILTER (WHERE title = ''), "
        "COUNT(*) FILTER (WHERE short = '') "
        "FROM isin_registry"
    ).fetchone()

    print(_APP_INTRO)
    print(f"Database file: {ISINRegistry.REG_FILE_ABSPATH}")
    print(f"Database size: {file_size:,} bytes")
    print(f"Records: {total:,}")
    print(f"Empty title: {empty_title:,}")
    print(f"Empty short: {empty_short:,}")
    input("\nPress Enter to finish...")
