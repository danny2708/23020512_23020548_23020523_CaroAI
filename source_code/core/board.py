from __future__ import annotations

from copy import deepcopy
from core.constants import EMPTY


class Board:
    """Represent a Caro board using a 2D list."""

    def __init__(self, size: int = 9, grid: list[list[str]] | None = None):
        if size < 9:
            raise ValueError("Board size must be at least 9x9 according to the assignment.")
        self.size = size
        self.grid = grid if grid is not None else [[EMPTY for _ in range(size)] for _ in range(size)]

    @classmethod
    def from_strings(cls, rows: list[str]) -> "Board":
        size = len(rows)
        grid = [list(row.strip()) for row in rows]
        return cls(size=size, grid=grid)

    def clone(self) -> "Board":
        return Board(size=self.size, grid=deepcopy(self.grid))

    def in_bounds(self, row: int, col: int) -> bool:
        return 0 <= row < self.size and 0 <= col < self.size

    def is_empty_cell(self, row: int, col: int) -> bool:
        return self.in_bounds(row, col) and self.grid[row][col] == EMPTY

    def place_move(self, row: int, col: int, player: str) -> bool:
        if not self.is_empty_cell(row, col):
            return False
        self.grid[row][col] = player
        return True

    def undo_move(self, row: int, col: int) -> None:
        if self.in_bounds(row, col):
            self.grid[row][col] = EMPTY

    def get_empty_cells(self) -> list[tuple[int, int]]:
        return [
            (r, c)
            for r in range(self.size)
            for c in range(self.size)
            if self.grid[r][c] == EMPTY
        ]

    def get_occupied_cells(self) -> list[tuple[int, int]]:
        return [
            (r, c)
            for r in range(self.size)
            for c in range(self.size)
            if self.grid[r][c] != EMPTY
        ]

    def is_full(self) -> bool:
        return all(self.grid[r][c] != EMPTY for r in range(self.size) for c in range(self.size))

    def print_board(self) -> None:
        print("   " + " ".join(f"{i:2d}" for i in range(self.size)))
        for i, row in enumerate(self.grid):
            print(f"{i:2d} " + "  ".join(row))
