from core.board import Board
from core.constants import DIRECTIONS, EMPTY, WIN_LENGTH
from core.rules import get_opponent


WIN_MOVE_SCORE = 10_000_000
BLOCK_WIN_SCORE = 9_000_000


class MoveGenerator:
    """Generate ordered legal/candidate moves.

    mode='all': return all empty cells.
    mode='nearby': return empty cells close to existing stones.
    """

    def __init__(
        self,
        mode: str = "nearby",
        radius: int = 1,
        max_candidates: int = 7,
        root_max_candidates: int = 10,
        deep_max_candidates: int = 4,
        deep_depth: int = 5,
        very_deep_max_candidates: int = 3,
        very_deep_depth: int = 7,
        ultra_deep_max_candidates: int = 2,
        ultra_deep_depth: int = 9,
    ):
        self.mode = mode
        self.radius = radius
        self.max_candidates = max_candidates
        self.root_max_candidates = root_max_candidates
        self.deep_max_candidates = deep_max_candidates
        self.deep_depth = deep_depth
        self.very_deep_max_candidates = very_deep_max_candidates
        self.very_deep_depth = very_deep_depth
        self.ultra_deep_max_candidates = ultra_deep_max_candidates
        self.ultra_deep_depth = ultra_deep_depth

    def generate(
        self,
        board: Board,
        player: str | None = None,
        ai_player: str | None = None,
        depth_remaining: int | None = None,
        search_depth: int | None = None,
        is_root: bool = False,
        priority_move: tuple[int, int] | None = None,
    ) -> list[tuple[int, int]]:
        if self.mode == "all":
            candidates = board.get_empty_cells()
        else:
            candidates = self._generate_nearby_moves(board)

        if player is None:
            return self._sort_by_center(board, candidates)

        ordered = self._order_moves(board, candidates, player)
        ordered = self._promote_priority_move(ordered, priority_move)
        return self._limit_moves(ordered, depth_remaining, search_depth, is_root)

    def _generate_nearby_moves(self, board: Board) -> list[tuple[int, int]]:
        occupied = board.get_occupied_cells()
        if not occupied:
            center = board.size // 2
            return [(center, center)]

        candidates: set[tuple[int, int]] = set()
        for row, col in occupied:
            for dr in range(-self.radius, self.radius + 1):
                for dc in range(-self.radius, self.radius + 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = row + dr, col + dc
                    if board.is_empty_cell(nr, nc):
                        candidates.add((nr, nc))

        return list(candidates)

    def _order_moves(
        self,
        board: Board,
        candidates: list[tuple[int, int]],
        player: str,
    ) -> list[tuple[int, int]]:
        scored_moves = [(self._quick_move_score(board, row, col, player), (row, col)) for row, col in candidates]
        scored_moves.sort(key=lambda item: item[0], reverse=True)
        return [move for _, move in scored_moves]

    def _quick_move_score(self, board: Board, row: int, col: int, player: str) -> int:
        opponent = get_opponent(player)
        attack_score = self._local_pattern_score(board, row, col, player)
        block_score = self._local_pattern_score(board, row, col, opponent)

        if attack_score >= WIN_MOVE_SCORE:
            return WIN_MOVE_SCORE * 2
        if block_score >= WIN_MOVE_SCORE:
            return BLOCK_WIN_SCORE

        center = (board.size - 1) / 2
        center_bonus = int((board.size - abs(row - center) - abs(col - center)) * 2)
        return attack_score * 2 + block_score * 3 + center_bonus

    def _local_pattern_score(self, board: Board, row: int, col: int, player: str) -> int:
        score = 0
        for dr, dc in DIRECTIONS:
            count, open_ends = self._line_metrics(board, row, col, player, dr, dc)
            score += self._score_line(count, open_ends)
        return score

    def _line_metrics(self, board: Board, row: int, col: int, player: str, dr: int, dc: int) -> tuple[int, int]:
        count = 1
        open_ends = 0

        nr, nc = row + dr, col + dc
        while board.in_bounds(nr, nc) and board.grid[nr][nc] == player:
            count += 1
            nr += dr
            nc += dc
        if board.in_bounds(nr, nc) and board.grid[nr][nc] == EMPTY:
            open_ends += 1

        nr, nc = row - dr, col - dc
        while board.in_bounds(nr, nc) and board.grid[nr][nc] == player:
            count += 1
            nr -= dr
            nc -= dc
        if board.in_bounds(nr, nc) and board.grid[nr][nc] == EMPTY:
            open_ends += 1

        return count, open_ends

    def _score_line(self, count: int, open_ends: int) -> int:
        if count >= WIN_LENGTH:
            return WIN_MOVE_SCORE
        if count == WIN_LENGTH - 1:
            return 150_000 if open_ends == 2 else 45_000
        if count == WIN_LENGTH - 2:
            return 4_000 if open_ends == 2 else 700
        if count == 1:
            return 10 * open_ends
        return 0

    def _limit_moves(
        self,
        ordered_moves: list[tuple[int, int]],
        depth_remaining: int | None,
        search_depth: int | None,
        is_root: bool,
    ) -> list[tuple[int, int]]:
        limit = self._candidate_limit(depth_remaining, search_depth, is_root)
        if limit <= 0 or len(ordered_moves) <= limit:
            return ordered_moves
        return ordered_moves[:limit]

    def _candidate_limit(self, depth_remaining: int | None, search_depth: int | None, is_root: bool) -> int:
        if search_depth is not None and search_depth >= self.ultra_deep_depth:
            if is_root:
                return min(self.root_max_candidates, 6)
            return self.ultra_deep_max_candidates
        if search_depth is not None and search_depth >= self.very_deep_depth:
            if is_root:
                return min(self.root_max_candidates, 8)
            return self.very_deep_max_candidates
        if search_depth is not None and search_depth >= self.deep_depth + 1:
            if is_root:
                return self.root_max_candidates
            return self.deep_max_candidates
        if is_root:
            return self.root_max_candidates
        if depth_remaining is not None and depth_remaining >= self.very_deep_depth:
            return self.very_deep_max_candidates
        if depth_remaining is not None and depth_remaining >= self.deep_depth:
            return self.deep_max_candidates
        return self.max_candidates

    def _promote_priority_move(
        self,
        ordered_moves: list[tuple[int, int]],
        priority_move: tuple[int, int] | None,
    ) -> list[tuple[int, int]]:
        if priority_move is None or priority_move not in ordered_moves:
            return ordered_moves
        return [priority_move] + [move for move in ordered_moves if move != priority_move]

    def _sort_by_center(self, board: Board, moves: list[tuple[int, int]]) -> list[tuple[int, int]]:
        center = (board.size - 1) / 2
        return sorted(moves, key=lambda move: abs(move[0] - center) + abs(move[1] - center))
