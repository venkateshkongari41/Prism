import hashlib
import json
from typing import Any


def build_cache_key(
    model: str,
    messages: list[dict[str, Any]],
) -> str:

    payload = {
        "model": model,
        "messages": messages,
    }

    serialized = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    )

    digest = hashlib.sha256(
        serialized.encode("utf-8")
    ).hexdigest()

    return f"prism:cache:{digest}"