from __future__ import annotations
from dataclasses import dataclass, field, asdict
import json


@dataclass(slots=True)
class Message:
    timestamp: str
    sender: str
    body: str
    line_number: int
    source_format: str = ""
    entities: list = field(default_factory=list)
    reply_to: int | None = None
    message_id: int | None = None

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)
