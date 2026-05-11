from __future__ import annotations

from dataclasses import dataclass

from core.board import Board
from core.constants import AI, HUMAN, EMPTY
from core.rules import check_winner, check_draw
from engine.ai_runner import create_ai
from ai.base_search import SearchResult


@dataclass
class AutoPlayStep:
    turn: int
    player: str
    move: tuple[int, int] | None
    score: int
    depth: int
    nodes_visited: int
    elapsed_time: float
    algorithm: str
    status_after_move: str


class AutoPlayGame:
    """Run AI-vs-AI games using the same search pipeline as Human-vs-AI.

    Current Minimax/Alpha-Beta implementation is written from O's perspective:
    O is MAX and X is MIN. To make X choose its own best move without duplicating
    the algorithms, we create a swapped copy of the board where X becomes O and
    O becomes X, run the selected searcher, then apply the returned coordinate as
    X on the real board.
    """

    def __init__(
        self,
        size: int = 9,
        x_mode: str = "minimax",
        o_mode: str = "alphabeta",
        depth: int = 2,
        max_turns: int | None = None,
    ):
        self.board = Board(size=size)
        self.x_ai = create_ai(x_mode)
        self.o_ai = create_ai(o_mode)
        self.depth = depth
        self.max_turns = max_turns or size * size
        self.history: list[AutoPlayStep] = []

    def status(self) -> str:
        if check_winner(self.board, HUMAN):
            return "X_WIN"
        if check_winner(self.board, AI):
            return "O_WIN"
        if check_draw(self.board):
            return "DRAW"
        return "ONGOING"

    def play(self, verbose: bool = True) -> str:
        current_player = HUMAN

        for turn in range(1, self.max_turns + 1):
            if self.status() != "ONGOING":
                break

            result = self._choose_move(current_player)
            if result.best_move is None:
                break

            row, col = result.best_move
            self.board.place_move(row, col, current_player)
            status_after = self.status()

            step = AutoPlayStep(
                turn=turn,
                player=current_player,
                move=result.best_move,
                score=result.score,
                depth=result.depth,
                nodes_visited=result.nodes_visited,
                elapsed_time=result.elapsed_time,
                algorithm=result.algorithm,
                status_after_move=status_after,
            )
            self.history.append(step)

            if verbose:
                print(
                    f"Turn {turn:02d} | Player {current_player} | "
                    f"{result.algorithm} | move={result.best_move} | "
                    f"score={result.score} | nodes={result.nodes_visited} | "
                    f"time={result.elapsed_time:.6f}s"
                )
                self.board.print_board()
                print()

            current_player = AI if current_player == HUMAN else HUMAN

        return self.status()

    def _choose_move(self, player: str) -> SearchResult:
        if player == AI:
            return self.o_ai.search(self.board, self.depth)

        swapped_board = self._swap_board_perspective(self.board)
        result = self.x_ai.search(swapped_board, self.depth)
        # Coordinate remains valid on the original board. Score is from X's
        # temporary perspective, so it is still useful for logging that AI's view.
        return result

    def _swap_board_perspective(self, board: Board) -> Board:
        swapped_grid = []
        for row in board.grid:
            swapped_row = []
            for cell in row:
                if cell == HUMAN:
                    swapped_row.append(AI)
                elif cell == AI:
                    swapped_row.append(HUMAN)
                else:
                    swapped_row.append(EMPTY)
            swapped_grid.append(swapped_row)
        return Board(size=board.size, grid=swapped_grid)
