from core.board import Board
from core.constants import AI, EMPTY, WIN_LENGTH, DIRECTIONS
from core.rules import get_opponent, get_terminal_score


class Evaluator:
    """Heuristic evaluator shared by Minimax and Alpha-Beta."""

    _windows_cache: dict[int, list[tuple[tuple[int, int], ...]]] = {}

    def __init__(self, cache_limit: int = 200_000):
        self.cache_limit = cache_limit
        self.cache: dict[tuple[int, str], int] = {}

    def evaluate(self, board: Board, ai_player: str = AI) -> int:
        terminal_score = get_terminal_score(board, ai_player)
        if terminal_score is not None:
            return terminal_score

        cache_key = (board.hash_key, ai_player)
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        opponent = get_opponent(ai_player)
        score = 0
        for window in self._get_windows(board.size):
            ai_count = 0
            opponent_count = 0
            empty_count = 0

            for row, col in window:
                value = board.grid[row][col]
                if value == ai_player:
                    ai_count += 1
                elif value == opponent:
                    opponent_count += 1
                elif value == EMPTY:
                    empty_count += 1

            if ai_count and opponent_count:
                continue
            if ai_count:
                score += self._score_counts(ai_count, empty_count)
            elif opponent_count:
                score -= self._score_counts(opponent_count, empty_count)

        if len(self.cache) >= self.cache_limit:
            self.cache.clear()
        self.cache[cache_key] = score
        return score

    @classmethod
    def _get_windows(cls, size: int) -> list[tuple[tuple[int, int], ...]]:
        windows = cls._windows_cache.get(size)
        if windows is not None:
            return windows

        windows = []
        for row in range(size):
            for col in range(size):
                for dr, dc in DIRECTIONS:
                    cells = []
                    for step in range(WIN_LENGTH):
                        nr = row + dr * step
                        nc = col + dc * step
                        if 0 <= nr < size and 0 <= nc < size:
                            cells.append((nr, nc))
                    if len(cells) == WIN_LENGTH:
                        windows.append(tuple(cells))

        cls._windows_cache[size] = windows
        return windows

    def _score_counts(self, player_count: int, empty_count: int) -> int:
        if player_count == WIN_LENGTH:
            return 100_000
        if player_count == WIN_LENGTH - 1 and empty_count == 1:
            return 1_000
        if player_count == WIN_LENGTH - 2 and empty_count == 2:
            return 100
        if player_count == 1 and empty_count == WIN_LENGTH - 1:
            return 10
        return 0
