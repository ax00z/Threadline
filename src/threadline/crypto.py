import hashlib
import json


# fields that go into the hash — everything except entities and hash metadata
_HASH_FIELDS = ("body", "line_number", "sender", "source_format", "timestamp")

_GENESIS = "0" * 64


def _canonical(msg: dict) -> str:
    """deterministic json for hashing — sorted keys, compact separators.
    Must match the Rust verifier format exactly."""
    subset = {k: msg[k] for k in _HASH_FIELDS if k in msg}
    return json.dumps(subset, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def build_chain(messages: list[dict]) -> list[dict]:
    prev = _GENESIS
    for i, msg in enumerate(messages):
        content_hash = _sha256(_canonical(msg))
        chain_hash = _sha256(content_hash + prev)
        msg["chain_hash"] = chain_hash
        msg["previous_hash"] = prev
        msg["chain_index"] = i
        prev = chain_hash
    return messages


def verify_chain(messages: list[dict]) -> dict:
    if not messages:
        return {"valid": True, "checked": 0, "broken_at": None}

    prev = _GENESIS
    for i, msg in enumerate(messages):
        stored = msg.get("chain_hash")
        if not stored:
            return {"valid": False, "checked": i, "broken_at": i}

        content_hash = _sha256(_canonical(msg))
        expected = _sha256(content_hash + prev)

        if expected != stored:
            return {"valid": False, "checked": i, "broken_at": i}

        # also check the previous_hash pointer matches
        if msg.get("previous_hash") != prev:
            return {"valid": False, "checked": i, "broken_at": i}

        prev = stored

    return {"valid": True, "checked": len(messages), "broken_at": None}
