from core.board import Board
from core.constants import AI, EMPTY, WIN_LENGTH, DIRECTIONS
from core.rules import get_opponent, get_terminal_score


class Evaluator:
    """Heuristic evaluator shared by Minimax and Alpha-Beta."""

    def evaluate(self, board: Board, ai_player: str = AI) -> int:
        terminal_score = get_terminal_score(board, ai_player)
        if terminal_score is not None:
            return terminal_score

        opponent = get_opponent(ai_player)
        ai_score = self._score_player(board, ai_player)
        opponent_score = self._score_player(board, opponent)
        return ai_score - opponent_score

    def _score_player(self, board: Board, player: str) -> int:
        score = 0
        n = board.size

        for r in range(n):
            for c in range(n):
                for dr, dc in DIRECTIONS:
                    cells = []
                    for k in range(WIN_LENGTH):
                        nr, nc = r + dr * k, c + dc * k
                        if 0 <= nr < n and 0 <= nc < n:
                            cells.append(board.grid[nr][nc])
                    if len(cells) == WIN_LENGTH:
                        score += self._score_window(cells, player)
        return score

    def _score_window(self, cells: list[str], player: str) -> int:
        opponent = get_opponent(player)
        player_count = cells.count(player)
        opponent_count = cells.count(opponent)
        empty_count = cells.count(EMPTY)

        if player_count > 0 and opponent_count > 0:
            return 0
        if player_count == 4:
            return 100_000
        if player_count == 3 and empty_count == 1:
            return 1_000
        if player_count == 2 and empty_count == 2:
            return 100
        if player_count == 1 and empty_count == 3:
            return 10
        return 0
