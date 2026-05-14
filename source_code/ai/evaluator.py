from core.board import Board, PLAYER_CODE
from core.constants import AI, EMPTY, WIN_LENGTH, DIRECTIONS
from core.rules import get_opponent, get_terminal_score

try:
    from accel import CYTHON_AVAILABLE, evaluate_codes
except ImportError:
    CYTHON_AVAILABLE = False
    evaluate_codes = None


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
        if CYTHON_AVAILABLE and evaluate_codes is not None:
            score = evaluate_codes(
                board.cell_codes,
                board.size,
                PLAYER_CODE[ai_player],
                PLAYER_CODE[opponent],
                WIN_LENGTH,
            )
        else:
            score = self._evaluate_python(board, ai_player, opponent)

        if len(self.cache) >= self.cache_limit:
            self.cache.clear()
        self.cache[cache_key] = score
        return score

    def score_breakdown(
        self,
        board: Board,
        ai_player: str = AI,
        evaluated_move: tuple[int, int] | None = None,
    ) -> dict[str, int]:
        """Return the heuristic components used by the benchmark EDA logs."""
        terminal_score = get_terminal_score(board, ai_player)
        if terminal_score is not None:
            return self._terminal_breakdown(terminal_score)

        opponent = get_opponent(ai_player)
        attack_score = 0
        defense_score = 0
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
                attack_score += self._score_counts(ai_count, empty_count)
            elif opponent_count:
                defense_score -= self._score_counts(opponent_count, empty_count)

        position_weight = self._position_weight(board, evaluated_move)
        final_score = attack_score + defense_score + position_weight
        return {
            "score_attack": attack_score,
            "score_defense": defense_score,
            "position_weight": position_weight,
            "final_heuristic_score": final_score,
        }

    def _evaluate_python(self, board: Board, ai_player: str, opponent: str) -> int:
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

    def _position_weight(self, board: Board, evaluated_move: tuple[int, int] | None) -> int:
        # The current assignment heuristic does not add positional weight to the final score.
        # Keep this component explicit so EDA can show that the deployed evaluator is pattern-based.
        return 0

    def _terminal_breakdown(self, terminal_score: int) -> dict[str, int]:
        if terminal_score > 0:
            attack_score = terminal_score
            defense_score = 0
        elif terminal_score < 0:
            attack_score = 0
            defense_score = terminal_score
        else:
            attack_score = 0
            defense_score = 0
        return {
            "score_attack": attack_score,
            "score_defense": defense_score,
            "position_weight": 0,
            "final_heuristic_score": terminal_score,
        }
