import math
import time

from ai.base_search import BaseSearch, SearchResult
from core.constants import AI
from core.rules import get_opponent, get_terminal_score


class MinimaxSearch(BaseSearch):
    def __init__(self, evaluator, move_generator):
        self.evaluator = evaluator
        self.move_generator = move_generator
        self.nodes_visited = 0

    def search(self, board, depth: int, ai_player: str = AI) -> SearchResult:
        self.nodes_visited = 0
        start = time.perf_counter()

        best_score = -math.inf
        best_move = None

        for move in self.move_generator.generate(board):
            row, col = move
            board.place_move(row, col, ai_player)
            score = self._minimax(
                board,
                depth - 1,
                current_player=get_opponent(ai_player),
                ai_player=ai_player,
            )
            board.undo_move(row, col)

            if score > best_score:
                best_score = score
                best_move = move

        if best_move is None:
            best_score = self.evaluator.evaluate(board, ai_player)

        elapsed = time.perf_counter() - start
        return SearchResult(
            best_move,
            int(best_score),
            depth,
            self.nodes_visited,
            elapsed,
            "Minimax",
            ai_player,
        )

    def _minimax(self, board, depth: int, current_player: str, ai_player: str) -> int:
        self.nodes_visited += 1

        terminal_score = get_terminal_score(board, ai_player)
        if terminal_score is not None:
            return terminal_score

        if depth == 0:
            return self.evaluator.evaluate(board, ai_player)

        moves = self.move_generator.generate(board)
        if not moves:
            return self.evaluator.evaluate(board, ai_player)

        next_player = get_opponent(current_player)
        if current_player == ai_player:
            value = -math.inf
            for row, col in moves:
                board.place_move(row, col, current_player)
                value = max(value, self._minimax(board, depth - 1, next_player, ai_player))
                board.undo_move(row, col)
            return int(value)

        value = math.inf
        for row, col in moves:
            board.place_move(row, col, current_player)
            value = min(value, self._minimax(board, depth - 1, next_player, ai_player))
            board.undo_move(row, col)
        return int(value)
