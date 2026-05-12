from dataclasses import dataclass
from typing import Optional

from core.constants import AI
from core.rules import get_opponent, get_terminal_score


@dataclass
class SearchResult:
    best_move: Optional[tuple[int, int]]
    score: int
    depth: int
    nodes_visited: int
    elapsed_time: float
    algorithm: str
    player: str


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

    def terminal_score(self, board, ai_player: str) -> int | None:
        return get_terminal_score(board, ai_player)
