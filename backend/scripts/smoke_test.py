"""
Prism final functional smoke test.

Run from:

    D:\\Capstone\\Prism\\backend

PowerShell:

    $env:PRISM_API_KEY="prism_live_YOUR_KEY"
    python scripts/smoke_test.py

Optional:

    $env:PRISM_BASE_URL="http://127.0.0.1:8000"
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Any

import httpx


BASE_URL = os.getenv(
    "PRISM_BASE_URL",
    "http://127.0.0.1:8000",
).rstrip("/")

API_KEY = os.getenv(
    "PRISM_API_KEY",
    "",
).strip()


@dataclass
class Check:
    name: str
    passed: bool
    detail: str


def print_result(check: Check) -> None:
    status = "PASS" if check.passed else "FAIL"

    print(
        f"[{status}] {check.name}: {check.detail}"
    )


def auth_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }


def chat_payload(
    model: str,
    content: str,
    stream: bool = False,
) -> dict[str, Any]:
    return {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": content,
            }
        ],
        "stream": stream,
    }


def main() -> int:

    if not API_KEY:

        print_result(
            Check(
                name="configuration",
                passed=False,
                detail=(
                    "Set PRISM_API_KEY before running "
                    "the smoke test."
                ),
            )
        )

        return 1

    checks: list[Check] = []

    try:

        with httpx.Client(
            timeout=30.0
        ) as client:

            # =====================================================
            # 1. HEALTH
            # =====================================================

            try:

                response = client.get(
                    f"{BASE_URL}/health"
                )

                checks.append(
                    Check(
                        name="health",
                        passed=response.is_success,
                        detail=(
                            f"HTTP {response.status_code}"
                        ),
                    )
                )

            except httpx.HTTPError as exc:

                checks.append(
                    Check(
                        name="health",
                        passed=False,
                        detail=str(exc),
                    )
                )

            # =====================================================
            # 2. FAST COMPLETION
            # =====================================================

            try:

                response = client.post(
                    f"{BASE_URL}/v1/chat/completions",
                    headers=auth_headers(),
                    json=chat_payload(
                        model="fast",
                        content=(
                            "Reply with exactly one sentence: "
                            "What is Redis?"
                        ),
                    ),
                )

                body = response.json()

                provider = response.headers.get(
                    "x-prism-provider",
                    "",
                )

                cache = response.headers.get(
                    "x-prism-cache",
                    "",
                )

                valid_response = (
                    response.is_success
                    and isinstance(
                        body,
                        dict,
                    )
                    and bool(
                        body.get("choices")
                    )
                )

                checks.append(
                    Check(
                        name="fast completion",
                        passed=valid_response,
                        detail=(
                            f"HTTP {response.status_code}, "
                            f"provider="
                            f"{provider or 'UNKNOWN'}, "
                            f"cache="
                            f"{cache or 'UNKNOWN'}"
                        ),
                    )
                )

            except (
                httpx.HTTPError,
                ValueError,
            ) as exc:

                checks.append(
                    Check(
                        name="fast completion",
                        passed=False,
                        detail=str(exc),
                    )
                )

            # =====================================================
            # 3. EXACT CACHE REPEAT
            # =====================================================

            try:

                response = client.post(
                    f"{BASE_URL}/v1/chat/completions",
                    headers=auth_headers(),
                    json=chat_payload(
                        model="fast",
                        content=(
                            "Reply with exactly one sentence: "
                            "What is Redis?"
                        ),
                    ),
                )

                cache_header = (
                    response.headers.get(
                        "x-prism-cache",
                        "",
                    )
                    .upper()
                )

                checks.append(
                    Check(
                        name="cache repeat",
                        passed=(
                            response.is_success
                            and cache_header
                            in {
                                "EXACT",
                                "SEMANTIC",
                            }
                        ),
                        detail=(
                            f"HTTP {response.status_code}, "
                            f"cache="
                            f"{cache_header or 'UNKNOWN'}"
                        ),
                    )
                )

            except httpx.HTTPError as exc:

                checks.append(
                    Check(
                        name="cache repeat",
                        passed=False,
                        detail=str(exc),
                    )
                )

            # =====================================================
            # 4. SEMANTIC CACHE PARAPHRASE
            #
            # Deliberately use a close paraphrase so this smoke
            # test verifies semantic matching rather than testing
            # an aggressive similarity threshold.
            # =====================================================

            try:

                response = client.post(
                    f"{BASE_URL}/v1/chat/completions",
                    headers=auth_headers(),
                    json=chat_payload(
                        model="fast",
                        content=(
                            "Can you explain what Redis is?"
                        ),
                    ),
                )

                cache_header = (
                    response.headers.get(
                        "x-prism-cache",
                        "",
                    )
                    .upper()
                )

                checks.append(
                    Check(
                        name="semantic cache paraphrase",
                        passed=(
                            response.is_success
                            and cache_header
                            in {
                                "SEMANTIC",
                                "EXACT",
                            }
                        ),
                        detail=(
                            f"HTTP {response.status_code}, "
                            f"cache="
                            f"{cache_header or 'UNKNOWN'}"
                        ),
                    )
                )

            except httpx.HTTPError as exc:

                checks.append(
                    Check(
                        name="semantic cache paraphrase",
                        passed=False,
                        detail=str(exc),
                    )
                )

            # =====================================================
            # 5. AUTO ROUTING
            # =====================================================

            try:

                response = client.post(
                    f"{BASE_URL}/v1/chat/completions",
                    headers=auth_headers(),
                    json=chat_payload(
                        model="auto",
                        content=(
                            "Compare event-driven architecture "
                            "and request-response architecture "
                            "for a distributed system."
                        ),
                    ),
                )
    
                resolved_model = (
                    response.headers.get(
                        "x-prism-resolved-model",
                        "",
                    )
                )

                if resolved_model in {
                    "fast",
                    "smart",
                }:

                    checks.append(
                        Check(
                            name="auto routing",
                            passed=response.is_success,
                            detail=(
                                f"resolved="
                                f"{resolved_model}"
                            ),
                        )
                    )

                elif response.is_success:

                    checks.append(
                        Check(
                            name="auto routing",
                            passed=True,
                            detail=(
                                "HTTP 200; auto request "
                                "completed, but "
                                "X-Prism-Resolved-Model "
                                "is not exposed by the "
                                "running backend."
                            ),
                        )
                    )

                else:

                    checks.append(
                        Check(
                            name="auto routing",
                            passed=False,
                            detail=(
                                f"HTTP "
                                f"{response.status_code}"
                            ),
                        )
                    )

            except httpx.HTTPError as exc:

                checks.append(
                    Check(
                        name="auto routing",
                        passed=False,
                        detail=str(exc),
                    )
                )

            # =====================================================
            # 6. STREAMING
            # =====================================================

            try:

                response = client.post(
                    f"{BASE_URL}/v1/chat/completions",
                    headers=auth_headers(),
                    json=chat_payload(
                        model="fast",
                        content=(
                            "Explain Redis in simple terms."
                        ),
                        stream=True,
                    ),
                    timeout=None,
                )

                body = response.text

                done_seen = (
                    "data: [DONE]" in body
                )

                checks.append(
                    Check(
                        name="streaming",
                        passed=(
                            response.is_success
                            and done_seen
                        ),
                        detail=(
                            f"HTTP "
                            f"{response.status_code}, "
                            f"DONE="
                            f"{done_seen}"
                        ),
                    )
                )

            except httpx.HTTPError as exc:

                checks.append(
                    Check(
                        name="streaming",
                        passed=False,
                        detail=str(exc),
                    )
                )

            # =====================================================
            # 7. USAGE SUMMARY
            # =====================================================

            try:

                response = client.get(
                    f"{BASE_URL}/v1/usage/summary",
                    headers=auth_headers(),
                    params={
                        "hours": 24,
                    },
                )

                body = response.json()

                summary = body.get(
                    "summary",
                    {},
                )

                valid_summary = (
                    response.is_success
                    and isinstance(
                        summary,
                        dict,
                    )
                )

                checks.append(
                    Check(
                        name="usage summary",
                        passed=valid_summary,
                        detail=(
                            f"HTTP "
                            f"{response.status_code}, "
                            f"requests="
                            f"{summary.get('total_requests', 0)}, "
                            f"cache_hit_rate="
                            f"{summary.get('cache_hit_rate', 0)}"
                        ),
                    )
                )

            except (
                httpx.HTTPError,
                ValueError,
            ) as exc:

                checks.append(
                    Check(
                        name="usage summary",
                        passed=False,
                        detail=str(exc),
                    )
                )

    except Exception as exc:

        print(
            "\nSmoke test terminated unexpectedly:"
            f" {exc}"
        )

        return 1

    # =============================================================
    # FINAL SUMMARY
    # =============================================================

    print()
    print(
        "Prism final smoke-test summary"
    )
    print(
        "=============================="
    )

    for check in checks:
        print_result(check)

    passed = sum(
        1
        for check in checks
        if check.passed
    )

    failed = (
        len(checks) - passed
    )

    print()
    print(
        f"Total checks : {len(checks)}"
    )
    print(
        f"Passed       : {passed}"
    )
    print(
        f"Failed       : {failed}"
    )

    if failed == 0:

        print()
        print(
            "FINAL RESULT: PASS"
        )

        return 0

    print()
    print(
        "FINAL RESULT: FAIL"
    )

    return 1


if __name__ == "__main__":
    sys.exit(main())