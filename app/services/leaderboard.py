from __future__ import annotations

from dataclasses import dataclass

from ..models import Player, WordleResult


@dataclass(frozen=True)
class LeaderboardRow:
    player_id: int
    player: str
    total_points: int
    average_guess_count: float | None
    daily_wins: int
    current_streak: int

    def as_dict(self) -> dict[str, int | float | str | None]:
        return {
            "player_id": self.player_id,
            "player": self.player,
            "total_points": self.total_points,
            "average_guess_count": self.average_guess_count,
            "daily_wins": self.daily_wins,
            "current_streak": self.current_streak,
        }


def build_leaderboard(players: list[Player]) -> list[LeaderboardRow]:
    daily_winners = _daily_winners([result for player in players for result in player.results])
    rows = [_build_player_row(player, daily_winners) for player in players]
    return sorted(
        rows,
        key=lambda row: (
            -row.total_points,
            -row.daily_wins,
            row.average_guess_count if row.average_guess_count is not None else float("inf"),
            row.player.lower(),
        ),
    )


def _build_player_row(player: Player, daily_winners: dict[int, set[int]]) -> LeaderboardRow:
    results = sorted(player.results, key=lambda result: result.wordle_number)
    completed_results = [result for result in results if result.guesses is not None]
    total_points = sum(result.points for result in results)
    average_guess_count = (
        round(sum(result.guesses for result in completed_results if result.guesses) / len(completed_results), 2)
        if completed_results
        else None
    )

    return LeaderboardRow(
        player_id=player.id,
        player=player.name,
        total_points=total_points,
        average_guess_count=average_guess_count,
        daily_wins=sum(1 for wordle_number, winners in daily_winners.items() if wordle_number in {r.wordle_number for r in results} and player.id in winners),
        current_streak=_calculate_current_streak(results),
    )


def _daily_winners(results: list[WordleResult]) -> dict[int, set[int]]:
    by_wordle: dict[int, list[WordleResult]] = {}
    for result in results:
        by_wordle.setdefault(result.wordle_number, []).append(result)

    winners: dict[int, set[int]] = {}
    for wordle_number, daily_results in by_wordle.items():
        successful = [result for result in daily_results if result.guesses is not None]
        if successful:
            best_guess_count = min(result.guesses for result in successful if result.guesses is not None)
            winners[wordle_number] = {
                result.player_id for result in successful if result.guesses == best_guess_count
            }
    return winners


def _calculate_current_streak(results: list[WordleResult]) -> int:
    if not results or results[-1].guesses is None:
        return 0

    successful_numbers = sorted(result.wordle_number for result in results if result.guesses is not None)
    streak = 1
    for previous, current in zip(reversed(successful_numbers[:-1]), reversed(successful_numbers)):
        if current - previous == 1:
            streak += 1
        else:
            break
    return streak
