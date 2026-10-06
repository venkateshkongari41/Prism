from dataclasses import dataclass

from app.core.model_resolver import model_resolver

import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1])
)


@dataclass
class EvaluationCase:
    name: str
    prompt: str
    expected: str


CASES = [
    EvaluationCase(
        name="Short + Easy",
        prompt="What is 2 + 2?",
        expected="fast",
    ),
    EvaluationCase(
        name="Short + Hard",
        prompt=(
            "Analyze the tradeoffs of distributed "
            "consensus algorithms."
        ),
        expected="smart",
    ),
    EvaluationCase(
        name="Long + Easy",
        prompt=(
            "Explain what HTTP is in simple terms. "
            "Describe how a browser sends a request "
            "to a server and receives a response. "
            "Explain the role of URLs, methods, headers, "
            "status codes, and JSON. "
            "Keep the explanation understandable for "
            "a beginner and provide simple examples."
        ),
        expected="fast",
    ),
    EvaluationCase(
        name="Long + Hard",
        prompt=(
            "Design a highly available distributed "
            "payment processing architecture. Analyze "
            "database consistency, idempotency, retries, "
            "message queues, failure recovery, horizontal "
            "scaling, caching, observability, security, "
            "and transaction ordering. Compare multiple "
            "architectural approaches and explain their "
            "tradeoffs, including how the system should "
            "behave during partial provider failures."
        ),
        expected="smart",
    ),
]


def length_only_baseline(
    prompt: str,
) -> str:
    """
    Simple baseline:
    short prompts -> fast
    long prompts  -> smart
    """

    word_count = len(prompt.split())

    if word_count >= 50:
        return "smart"

    return "fast"


def evaluate():

    prism_correct = 0
    baseline_correct = 0

    print()
    print("=" * 70)
    print("PRISM SMART ROUTER EVALUATION")
    print("=" * 70)

    for case in CASES:

        messages = [
            {
                "role": "user",
                "content": case.prompt,
            }
        ]

        prism_result = (
            model_resolver.resolve_alias(
                "auto",
                messages,
            )
        )

        baseline_result = (
            length_only_baseline(
                case.prompt
            )
        )

        prism_ok = (
            prism_result == case.expected
        )

        baseline_ok = (
            baseline_result == case.expected
        )

        if prism_ok:
            prism_correct += 1

        if baseline_ok:
            baseline_correct += 1

        print()
        print(f"Case:       {case.name}")
        print(f"Expected:   {case.expected}")
        print(f"Baseline:   {baseline_result}")
        print(f"Prism auto: {prism_result}")
        print(
            f"Prism:      "
            f"{'PASS' if prism_ok else 'FAIL'}"
        )
        print(
            f"Baseline:   "
            f"{'PASS' if baseline_ok else 'FAIL'}"
        )

    total = len(CASES)

    prism_accuracy = (
        prism_correct / total
    ) * 100

    baseline_accuracy = (
        baseline_correct / total
    ) * 100

    improvement = (
        prism_accuracy
        - baseline_accuracy
    )

    print()
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)

    print(
        f"Length-only baseline accuracy: "
        f"{baseline_accuracy:.1f}%"
    )

    print(
        f"Prism auto-router accuracy:    "
        f"{prism_accuracy:.1f}%"
    )

    print(
        f"Improvement:                   "
        f"{improvement:+.1f}%"
    )

    print("=" * 70)


if __name__ == "__main__":
    evaluate()