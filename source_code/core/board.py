from __future__ import annotations

import random

from core.constants import AI, EMPTY, HUMAN


PLAYER_INDEX = {
    HUMAN: 0,
    AI: 1,
}


class Board:
    """Represent a Caro board using a 2D list."""

    _zobrist_tables: dict[int, list[list[list[int]]]] = {}

    def __init__(
        self,
        size: int = 9,
        grid: list[list[str]] | None = None,
        move_stack: list[tuple[int, int, str]] | None = None,
    ):
        if size < 9:
            raise ValueError("Board size must be at least 9x9 according to the assignment.")
        if grid is not None and len(grid) != size:
            raise ValueError("Grid row count must match board size.")

        self.size = size
        self.grid = [row[:] for row in grid] if grid is not None else [[EMPTY for _ in range(size)] for _ in range(size)]
        self.occupied_cells: set[tuple[int, int]] = set()
        self.move_stack = list(move_stack or [])
        self.hash_key = 0
        self._zobrist = self._get_zobrist_table(size)
        self._rebuild_metadata()

    @classmethod
    def from_strings(cls, rows: list[str]) -> "Board":
        size = len(rows)
        grid = [list(row.strip()) for row in rows]
        return cls(size=size, grid=grid)

    def clone(self) -> "Board":
        return Board(size=self.size, grid=self.grid, move_stack=self.move_stack)

    @classmethod
    def _get_zobrist_table(cls, size: int) -> list[list[list[int]]]:
        table = cls._zobrist_tables.get(size)
        if table is not None:
            return table

        rng = random.Random(20260512 + size)
        table = [
            [[rng.getrandbits(64), rng.getrandbits(64)] for _ in range(size)]
            for _ in range(size)
        ]
        cls._zobrist_tables[size] = table
        return table

    def _rebuild_metadata(self) -> None:
        self.occupied_cells.clear()
        self.hash_key = 0
        for row in range(self.size):
            if len(self.grid[row]) != self.size:
                raise ValueError("Grid column count must match board size.")
            for col in range(self.size):
                value = self.grid[row][col]
                if value == EMPTY:
                    continue
                self.occupied_cells.add((row, col))
                self.hash_key ^= self._zobrist[row][col][PLAYER_INDEX[value]]

    def in_bounds(self, row: int, col: int) -> bool:
        return 0 <= row < self.size and 0 <= col < self.size

    def is_empty_cell(self, row: int, col: int) -> bool:
        return self.in_bounds(row, col) and self.grid[row][col] == EMPTY

    def place_move(self, row: int, col: int, player: str) -> bool:
        if not self.is_empty_cell(row, col):
            return False
        self.grid[row][col] = player
        self.occupied_cells.add((row, col))
        self.move_stack.append((row, col, player))
        self.hash_key ^= self._zobrist[row][col][PLAYER_INDEX[player]]
        return True

    def undo_move(self, row: int, col: int) -> None:
        if not self.in_bounds(row, col):
            return

        player = self.grid[row][col]
        if player == EMPTY:
            return

        self.grid[row][col] = EMPTY
        self.occupied_cells.discard((row, col))
        self.hash_key ^= self._zobrist[row][col][PLAYER_INDEX[player]]
        if self.move_stack and self.move_stack[-1][:2] == (row, col):
            self.move_stack.pop()
            return

        for index in range(len(self.move_stack) - 1, -1, -1):
            if self.move_stack[index][:2] == (row, col):
                del self.move_stack[index]
                break

    def last_move(self) -> tuple[int, int, str] | None:
        if not self.move_stack:
            return None
        return self.move_stack[-1]

    def get_empty_cells(self) -> list[tuple[int, int]]:
        return [
            (r, c)
            for r in range(self.size)
            for c in range(self.size)
            if self.grid[r][c] == EMPTY
        ]

    def get_occupied_cells(self) -> list[tuple[int, int]]:
        return sorted(self.occupied_cells)

    def is_full(self) -> bool:
        return len(self.occupied_cells) == self.size * self.size

    def to_strings(self) -> list[str]:
        return ["".join(row) for row in self.grid]

    def to_ascii(self) -> str:
        lines = ["   " + " ".join(f"{i:2d}" for i in range(self.size))]
        for row_index, row in enumerate(self.grid):
            lines.append(f"{row_index:2d} " + "  ".join(row))
        return "\n".join(lines)

    def print_board(self) -> None:
        print(self.to_ascii())
