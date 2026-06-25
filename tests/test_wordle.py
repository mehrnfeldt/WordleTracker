import pytest

from app.services.wordle import WordleParseError, calculate_points, parse_wordle_message


@pytest.mark.parametrize(
    ("raw_score", "points"),
    [
        ("1/6", 10),
        ("2/6", 8),
        ("3/6", 6),
        ("4/6", 4),
        ("5/6", 2),
        ("6/6", 1),
        ("X/6", 0),
    ],
)
def test_calculate_points(raw_score, points):
    assert calculate_points(raw_score) == points


def test_parse_standard_wordle_message():
    result = parse_wordle_message("Wordle 1466 3/6")

    assert result.wordle_number == 1466
    assert result.raw_score == "3/6"
    assert result.guesses == 3
    assert result.points == 6


def test_parse_failed_wordle_message():
    result = parse_wordle_message("Wordle 1466 X/6")

    assert result.wordle_number == 1466
    assert result.raw_score == "X/6"
    assert result.guesses is None
    assert result.points == 0


def test_rejects_invalid_message():
    with pytest.raises(WordleParseError):
        parse_wordle_message("I got it in three today")
