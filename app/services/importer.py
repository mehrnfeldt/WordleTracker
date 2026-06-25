from __future__ import annotations

from dataclasses import dataclass

from ..models import Player
from .wordle import WORDLE_PATTERN


@dataclass(frozen=True)
class ImportCandidate:
    player: Player | None
    sender: str | None
    message: str
    line_number: int


def extract_import_candidates(text: str, players: list[Player]) -> list[ImportCandidate]:
    players_by_name = {player.name.casefold(): player for player in players}
    players_by_phone = {player.phone_number: player for player in players}
    candidates: list[ImportCandidate] = []
    current_sender: str | None = None

    for index, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue

        match = WORDLE_PATTERN.search(line)
        if not match:
            current_sender = _clean_sender(line)
            continue

        sender = _sender_from_wordle_line(line, match.start()) or current_sender
        candidates.append(
            ImportCandidate(
                player=_find_player(sender, players_by_name, players_by_phone),
                sender=sender,
                message=line[match.start() :],
                line_number=index,
            )
        )

    return candidates


def _sender_from_wordle_line(line: str, wordle_start: int) -> str | None:
    prefix = line[:wordle_start].strip()
    return _clean_sender(prefix) if prefix else None


def _clean_sender(value: str) -> str:
    return value.strip(" :-\t")


def _find_player(
    sender: str | None,
    players_by_name: dict[str, Player],
    players_by_phone: dict[str, Player],
) -> Player | None:
    if not sender:
        return None
    return players_by_phone.get(sender) or players_by_name.get(sender.casefold())
