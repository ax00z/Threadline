from __future__ import annotations

import duckdb


class MessageStore:

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
        # only allow reads
        stripped = sql.strip().rstrip(";")
        first_word = stripped.split()[0].upper() if stripped else ""
        if first_word not in ("SELECT", "WITH", "EXPLAIN"):
            return {
                "error": "Only SELECT queries are allowed.",
                "columns": [],
                "rows": [],
                "row_count": 0,
            }

        # slap a limit on if they didn't
        upper = stripped.upper()
        if "LIMIT" not in upper:
            stripped = f"{stripped} LIMIT {limit}"

        try:
            result = self._con.execute(stripped)
            columns = [desc[0] for desc in result.description]
            rows = result.fetchall()
            # duckdb returns weird types sometimes
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
