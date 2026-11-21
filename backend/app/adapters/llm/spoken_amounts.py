"""Build numeric balance choices exclusively from the agent's transcript."""

import re
from collections.abc import Iterable
from decimal import Decimal

_SMALL = dict(zip(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen "
    "sixteen seventeen eighteen nineteen".split(), range(20), strict=True,
))
_SMALL.update(zip("twenty thirty forty fifty sixty seventy eighty ninety".split(), range(20, 100, 10), strict=True))
_TOKEN = "|".join((*_SMALL, "hundred", "thousand", "million", "a", "and"))
_WORDS = rf"(?:{_TOKEN})(?:[ -]+(?:{_TOKEN}))*"
_DIGITS = r"\d+(?:,\d{3})*(?:\.\d+)?"
_NUMBER = rf"(?:{_DIGITS}|{_WORDS})"
_MONEY = re.compile(
    rf"\b(?P<whole>{_NUMBER})\s+dollars?(?:\s+(?:and\s+)?(?P<cents>{_NUMBER})\s+cents?)?\b"
    rf"|\b(?P<only_cents>{_NUMBER})\s+cents?\b|(?P<digits>{_DIGITS})", re.I,
)


def _number(phrase: str) -> Decimal:
    if phrase[0].isdigit():
        return Decimal(phrase.replace(",", ""))
    total = group = 0
    for word in phrase.casefold().replace("-", " ").split():
        if word == "hundred":
            group = (group or 1) * 100
        elif word in ("thousand", "million"):
            total += (group or 1) * (1000 if word == "thousand" else 1_000_000)
            group = 0
        else:
            group += _SMALL.get(word, int(word == "a"))
    return Decimal(total + group)


def amount_candidates(turns: Iterable[str]) -> tuple[str, ...]:
    """Offer spoken currency phrases and written numbers in their order of appearance."""
    values = {}
    for turn in turns:
        for match in _MONEY.finditer(turn):
            raw = match["whole"] or match["digits"]
            cents = match["cents"] or match["only_cents"]
            value = _number(raw) if raw else Decimal(0)
            if cents:
                value += _number(cents) / 100
            values[format(value.normalize(), "f")] = None
    return tuple(values)
