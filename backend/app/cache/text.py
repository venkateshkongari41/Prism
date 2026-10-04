from typing import Any


def messages_to_text(
    messages: list[dict[str, Any]],
) -> str:

    parts: list[str] = []

    for message in messages:

        role = message.get(
            "role",
            "",
        )

        content = message.get(
            "content",
            "",
        )

        parts.append(
            f"{role}: {content}"
        )

    return "\n".join(parts)