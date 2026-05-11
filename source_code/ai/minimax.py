import math
import time

from ai.base_search import BaseSearch, SearchResult
from core.constants import AI, HUMAN
from core.rules import get_terminal_score


class MinimaxSearch(BaseSearch):
    def __init__(self, evaluator, move_generator):
        self.evaluator = evaluator
        self.move_generator = move_generator
        self.nodes_visited = 0

    def search(self, board, depth: int) -> SearchResult:
        self.nodes_visited = 0
        start = time.perf_counter()

        best_score = -math.inf
        best_move = None

        for move in self.move_generator.generate(board):
            row, col = move
            board.place_move(row, col, AI)
            score = self._minimax(board, depth - 1, maximizing_player=False)
            board.undo_move(row, col)

            if score > best_score:
                best_score = score
                best_move = move

        elapsed = time.perf_counter() - start
        return SearchResult(best_move, int(best_score), depth, self.nodes_visited, elapsed, "Minimax")

    def _minimax(self, board, depth: int, maximizing_player: bool) -> int:
        self.nodes_visited += 1

        terminal_score = get_terminal_score(board)
        if terminal_score is not None:
            return terminal_score

        if depth == 0:
            return self.evaluator.evaluate(board)

        moves = self.move_generator.generate(board)
        if maximizing_player:
            value = -math.inf
            for row, col in moves:
                board.place_move(row, col, AI)
                value = max(value, self._minimax(board, depth - 1, False))
                board.undo_move(row, col)
            return int(value)

        value = math.inf
        for row, col in moves:
            board.place_move(row, col, HUMAN)
            value = min(value, self._minimax(board, depth - 1, True))
            board.undo_move(row, col)
        return int(value)
