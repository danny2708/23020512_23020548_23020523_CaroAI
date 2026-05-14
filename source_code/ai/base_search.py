from dataclasses import dataclass, field
from typing import Optional

from core.constants import AI, TERMINAL_WIN_SCORE
from core.rules import find_winning_moves, get_opponent, get_terminal_score


@dataclass
class SearchResult:
    best_move: Optional[tuple[int, int]]
    score: int
    depth: int
    nodes_visited: int
    elapsed_time: float
    algorithm: str
    player: str
    pruning_events: list[dict] = field(default_factory=list)


@dataclass(slots=True)
class TranspositionEntry:
    depth: int
    score: int
    flag: str = "EXACT"
    best_move: Optional[tuple[int, int]] = None


class BaseSearch:
    def search(self, board, depth: int, ai_player: str = AI) -> SearchResult:
        raise NotImplementedError

    def opponent(self, player: str) -> str:
        return get_opponent(player)

    def terminal_score(self, board, ai_player: str, depth_remaining: int = 0) -> int | None:
        return get_terminal_score(board, ai_player, depth_remaining=depth_remaining)

    def immediate_win_score(
        self,
        board,
        moves: list[tuple[int, int]],
        current_player: str,
        ai_player: str,
        depth_remaining: int = 0,
    ) -> int | None:
        move_generator = getattr(self, "move_generator", None)
        if move_generator is not None and hasattr(move_generator, "winning_moves"):
            winning_moves = move_generator.winning_moves(board, moves, current_player)
        else:
            winning_moves = find_winning_moves(board, current_player, moves)

        if not winning_moves:
            return None
        bonus = max(0, depth_remaining)
        if current_player == ai_player:
            return TERMINAL_WIN_SCORE + bonus
        return -TERMINAL_WIN_SCORE - bonus
