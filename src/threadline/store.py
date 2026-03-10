"""
DuckDB-backed analytical message store.

Provides SQL query capability over parsed messages. The database lives
entirely in-memory (no files written to disk) — suitable for forensic
workflows where evidence must not be persisted without explicit consent.
"""

from __future__ import annotations

import duckdb


class MessageStore:
    """In-memory DuckDB store for message analytics."""

    def __init__(self) -> None:
        self._con = duckdb.connect(":memory:")
        self._con.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                row_id      INTEGER,
                timestamp   VARCHAR,
                sender      VARCHAR,
                body        VARCHAR,
                line_number INTEGER,
                source_format VARCHAR
            )
        """)

    def load(self, messages: list[dict]) -> int:
        """Bulk-load parsed messages into the store. Returns row count."""
        self._con.execute("DELETE FROM messages")
        self._con.executemany(
            "INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?)",
            [
                (
                    i,
                    m.get("timestamp", ""),
                    m.get("sender", ""),
                    m.get("body", ""),
                    m.get("line_number", 0),
                    m.get("source_format", ""),
                )
                for i, m in enumerate(messages)
            ],
        )
        return len(messages)

    def query(self, sql: str, limit: int = 500) -> dict:
        """
        Execute a read-only SQL query against the messages table.

        Returns {columns: [...], rows: [[...], ...], row_count: int}.
        Automatically wraps in a LIMIT if none is present.
        """
        # Safety: only allow SELECT statements
        stripped = sql.strip().rstrip(";")
        first_word = stripped.split()[0].upper() if stripped else ""
        if first_word not in ("SELECT", "WITH", "EXPLAIN"):
            return {
                "error": "Only SELECT queries are allowed.",
                "columns": [],
                "rows": [],
                "row_count": 0,
            }

        # Add LIMIT if not present
        upper = stripped.upper()
        if "LIMIT" not in upper:
            stripped = f"{stripped} LIMIT {limit}"

        try:
            result = self._con.execute(stripped)
            columns = [desc[0] for desc in result.description]
            rows = result.fetchall()
            # Convert to JSON-safe types
            safe_rows = [
                [str(cell) if cell is not None else None for cell in row]
                for row in rows
            ]
            return {
                "columns": columns,
                "rows": safe_rows,
                "row_count": len(safe_rows),
            }
        except Exception as e:
            return {
                "error": str(e),
                "columns": [],
                "rows": [],
                "row_count": 0,
            }

    def close(self) -> None:
        self._con.close()
