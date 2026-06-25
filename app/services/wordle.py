from __future__ import annotations

import re
from dataclasses import dataclass


WORDLE_PATTERN = re.compile(r"\bWordle\s+(?P<number>\d+)\s+(?P<score>[1-6Xx]/6)\b")
POINTS_BY_SCORE = {
    "1/6": 10,
    "2/6": 8,
    "3/6": 6,
    "4/6": 4,
    "5/6": 2,
    "6/6": 1,
    "X/6": 0,
}


class WordleParseError(ValueError):
    pass


@dataclass(frozen=True)
class ParsedWordleResult:
    wordle_number: int
    raw_score: str
    guesses: int | None
    points: int


def calculate_points(raw_score: str) -> int:
    normalized = raw_score.upper()
    if normalized not in POINTS_BY_SCORE:
        raise WordleParseError(f"Unsupported Wordle score: {raw_score}")
    return POINTS_BY_SCORE[normalized]


def parse_wordle_message(message: str) -> ParsedWordleResult:
    match = WORDLE_PATTERN.search(message.strip())
    if not match:
        raise WordleParseError("Message does not contain a valid Wordle result.")

    raw_score = match.group("score").upper()
    guesses = None if raw_score == "X/6" else int(raw_score[0])

    return ParsedWordleResult(
        wordle_number=int(match.group("number")),
        raw_score=raw_score,
        guesses=guesses,
        points=calculate_points(raw_score),
    )
