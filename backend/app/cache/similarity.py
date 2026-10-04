import math


def cosine_similarity(
    first: list[float],
    second: list[float],
) -> float:

    if not first or not second:
        return 0.0

    if len(first) != len(second):
        return 0.0

    dot_product = sum(
        a * b
        for a, b in zip(
            first,
            second,
        )
    )

    first_norm = math.sqrt(
        sum(
            value * value
            for value in first
        )
    )

    second_norm = math.sqrt(
        sum(
            value * value
            for value in second
        )
    )

    if first_norm == 0 or second_norm == 0:
        return 0.0

    return (
        dot_product
        / (first_norm * second_norm)
    )