from core.board import Board


class MoveGenerator:
    """Generate legal/candidate moves.

    mode='all': return all empty cells.
    mode='nearby': return empty cells close to existing stones.
    """

    def __init__(self, mode: str = "nearby", radius: int = 1):
        self.mode = mode
        self.radius = radius

    def generate(self, board: Board) -> list[tuple[int, int]]:
        if self.mode == "all":
            return board.get_empty_cells()
        return self._generate_nearby_moves(board)

    def _generate_nearby_moves(self, board: Board) -> list[tuple[int, int]]:
        occupied = board.get_occupied_cells()
        if not occupied:
            center = board.size // 2
            return [(center, center)]

        candidates: set[tuple[int, int]] = set()
        for r, c in occupied:
            for dr in range(-self.radius, self.radius + 1):
                for dc in range(-self.radius, self.radius + 1):
                    nr, nc = r + dr, c + dc
                    if board.is_empty_cell(nr, nc):
                        candidates.add((nr, nc))

        center = (board.size - 1) / 2
        return sorted(candidates, key=lambda move: abs(move[0] - center) + abs(move[1] - center))
