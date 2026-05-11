from dataclasses import dataclass
from typing import Optional


@dataclass
class SearchResult:
    best_move: Optional[tuple[int, int]]
    score: int
    depth: int
    nodes_visited: int
    elapsed_time: float
    algorithm: str


class BaseSearch:
    def search(self, board, depth: int) -> SearchResult:
        raise NotImplementedError
