import math
import time

from ai.base_search import BaseSearch, SearchResult, TranspositionEntry
from core.constants import AI
from core.rules import get_opponent, get_terminal_score


class AlphaBetaSearch(BaseSearch):
    def __init__(self, evaluator, move_generator, table_limit: int = 250_000):
        self.evaluator = evaluator
        self.move_generator = move_generator
        self.nodes_visited = 0
        self.table_limit = table_limit
        self.transposition_table: dict[tuple[int, str, str], TranspositionEntry] = {}

    def search(self, board, depth: int, ai_player: str = AI) -> SearchResult:
        self.nodes_visited = 0
        depth = max(1, depth)
        start = time.perf_counter()

        terminal_score = get_terminal_score(board, ai_player)
        if terminal_score is not None:
            elapsed = time.perf_counter() - start
            return SearchResult(None, terminal_score, depth, 0, elapsed, "Alpha-Beta", ai_player)

        best_score = -math.inf
        best_move = None
        alpha = -math.inf
        beta = math.inf

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
            score = self._alpha_beta(
                board,
                depth - 1,
                alpha,
                beta,
                current_player=get_opponent(ai_player),
                ai_player=ai_player,
                search_depth=depth,
            )
            board.undo_move(row, col)

            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, best_score)

        if best_move is None:
            best_score = self.evaluator.evaluate(board, ai_player)

        elapsed = time.perf_counter() - start
        return SearchResult(
            best_move,
            int(best_score),
            depth,
            self.nodes_visited,
            elapsed,
            "Alpha-Beta",
            ai_player,
        )

    def _alpha_beta(
        self,
        board,
        depth: int,
        alpha: float,
        beta: float,
        current_player: str,
        ai_player: str,
        search_depth: int,
    ) -> int:
        self.nodes_visited += 1

        terminal_score = get_terminal_score(board, ai_player)
        if terminal_score is not None:
            return terminal_score

        if depth <= 0:
            return self.evaluator.evaluate(board, ai_player)

        key = (board.hash_key, current_player, ai_player)
        original_alpha = alpha
        original_beta = beta
        entry = self.transposition_table.get(key)
        if entry is not None and entry.depth >= depth:
            if entry.flag == "EXACT":
                return entry.score
            if entry.flag == "LOWERBOUND":
                alpha = max(alpha, entry.score)
            elif entry.flag == "UPPERBOUND":
                beta = min(beta, entry.score)
            if alpha >= beta:
                return entry.score

        moves = self.move_generator.generate(
            board,
            player=current_player,
            ai_player=ai_player,
            depth_remaining=depth,
            search_depth=search_depth,
            priority_move=entry.best_move if entry is not None else None,
        )
        if not moves:
            return self.evaluator.evaluate(board, ai_player)

        next_player = get_opponent(current_player)
        if current_player == ai_player:
            value = -math.inf
            best_move = moves[0]
            for row, col in moves:
                board.place_move(row, col, current_player)
                score = self._alpha_beta(board, depth - 1, alpha, beta, next_player, ai_player, search_depth)
                board.undo_move(row, col)
                if score > value:
                    value = score
                    best_move = (row, col)
                alpha = max(alpha, value)
                if beta <= alpha:
                    break
        else:
            value = math.inf
            best_move = moves[0]
            for row, col in moves:
                board.place_move(row, col, current_player)
                score = self._alpha_beta(board, depth - 1, alpha, beta, next_player, ai_player, search_depth)
                board.undo_move(row, col)
                if score < value:
                    value = score
                    best_move = (row, col)
                beta = min(beta, value)
                if beta <= alpha:
                    break

        value = int(value)
        flag = "EXACT"
        if value <= original_alpha:
            flag = "UPPERBOUND"
        elif value >= original_beta:
            flag = "LOWERBOUND"
        self._store_entry(key, depth, value, flag, best_move)
        return value

    def _store_entry(
        self,
        key: tuple[int, str, str],
        depth: int,
        score: int,
        flag: str,
        best_move: tuple[int, int] | None,
    ) -> None:
        if len(self.transposition_table) >= self.table_limit:
            self.transposition_table.clear()
        self.transposition_table[key] = TranspositionEntry(
            depth=depth,
            score=score,
            flag=flag,
            best_move=best_move,
        )
