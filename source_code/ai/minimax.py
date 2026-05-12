import math
import time

from ai.base_search import BaseSearch, SearchResult, TranspositionEntry
from core.constants import AI
from core.rules import get_opponent, get_terminal_score


class MinimaxSearch(BaseSearch):
    def __init__(self, evaluator, move_generator, table_limit: int = 250_000):
        self.evaluator = evaluator
        self.move_generator = move_generator
        self.nodes_visited = 0
        self.table_limit = table_limit
        self.transposition_table: dict[tuple[int, int, str, str], TranspositionEntry] = {}

    def search(self, board, depth: int, ai_player: str = AI) -> SearchResult:
        self.nodes_visited = 0
        depth = max(1, depth)
        start = time.perf_counter()

        terminal_score = get_terminal_score(board, ai_player)
        if terminal_score is not None:
            elapsed = time.perf_counter() - start
            return SearchResult(None, terminal_score, depth, 0, elapsed, "Minimax", ai_player)

        best_score = -math.inf
        best_move = None

        moves = self.move_generator.generate(
            board,
            player=ai_player,
            ai_player=ai_player,
            depth_remaining=depth,
            search_depth=depth,
            is_root=True,
        )
        for move in moves:
            row, col = move
            board.place_move(row, col, ai_player)
            score = self._minimax(
                board,
                depth - 1,
                current_player=get_opponent(ai_player),
                ai_player=ai_player,
                search_depth=depth,
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

    def _minimax(self, board, depth: int, current_player: str, ai_player: str, search_depth: int) -> int:
        self.nodes_visited += 1

        terminal_score = get_terminal_score(board, ai_player)
        if terminal_score is not None:
            return terminal_score

        if depth <= 0:
            return self.evaluator.evaluate(board, ai_player)

        key = (board.hash_key, depth, current_player, ai_player)
        entry = self.transposition_table.get(key)
        if entry is not None:
            return entry.score

        moves = self.move_generator.generate(
            board,
            player=current_player,
            ai_player=ai_player,
            depth_remaining=depth,
            search_depth=search_depth,
        )
        if not moves:
            return self.evaluator.evaluate(board, ai_player)

        next_player = get_opponent(current_player)
        if current_player == ai_player:
            value = -math.inf
            best_move = moves[0]
            for row, col in moves:
                board.place_move(row, col, current_player)
                score = self._minimax(board, depth - 1, next_player, ai_player, search_depth)
                board.undo_move(row, col)
                if score > value:
                    value = score
                    best_move = (row, col)
        else:
            value = math.inf
            best_move = moves[0]
            for row, col in moves:
                board.place_move(row, col, current_player)
                score = self._minimax(board, depth - 1, next_player, ai_player, search_depth)
                board.undo_move(row, col)
                if score < value:
                    value = score
                    best_move = (row, col)

        value = int(value)
        self._store_entry(key, depth, value, best_move)
        return value

    def _store_entry(
        self,
        key: tuple[int, int, str, str],
        depth: int,
        score: int,
        best_move: tuple[int, int] | None,
    ) -> None:
        if len(self.transposition_table) >= self.table_limit:
            self.transposition_table.clear()
        self.transposition_table[key] = TranspositionEntry(depth=depth, score=score, best_move=best_move)
