from __future__ import annotations

from dataclasses import dataclass

from core.board import Board
from core.constants import AI, HUMAN
from core.rules import check_winner, check_draw
from engine.ai_runner import create_ai, normalize_ai_mode
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
    """Run AI-vs-AI games using the same search pipeline as Human-vs-AI."""

    def __init__(
        self,
        size: int = 9,
        x_mode: str = "minimax",
        o_mode: str = "alphabeta",
        depth: int = 2,
        max_turns: int | None = None,
    ):
        self.board = Board(size=size)
        self.x_mode = normalize_ai_mode(x_mode)
        self.o_mode = normalize_ai_mode(o_mode)
        self.x_ai = create_ai(self.x_mode)
        self.o_ai = create_ai(self.o_mode)
        self.depth = depth
        self.max_turns = max_turns or size * size
        self.history: list[AutoPlayStep] = []
        self.current_player = HUMAN

    def status(self) -> str:
        if check_winner(self.board, HUMAN):
            return "X_WIN"
        if check_winner(self.board, AI):
            return "O_WIN"
        if check_draw(self.board):
            return "DRAW"
        return "ONGOING"

    def play(self, verbose: bool = True) -> str:
        while self.status() == "ONGOING" and len(self.history) < self.max_turns:
            step = self.step()
            if step is None:
                break

            if verbose:
                print(
                    f"Turn {step.turn:02d} | Player {step.player} | "
                    f"{step.algorithm} | move={step.move} | "
                    f"score={step.score} | depth={step.depth} | nodes={step.nodes_visited} | "
                    f"time={step.elapsed_time:.6f}s"
                )
                self.board.print_board()
                print()

        return self.status()

    def step(self) -> AutoPlayStep | None:
        if self.status() != "ONGOING" or len(self.history) >= self.max_turns:
            return None

        player = self.current_player
        result = self._choose_move(player)
        if result.best_move is None:
            return None

        row, col = result.best_move
        if not self.board.place_move(row, col, player):
            return None
        status_after = self.status()

        step = AutoPlayStep(
            turn=len(self.history) + 1,
            player=player,
            move=result.best_move,
            score=result.score,
            depth=result.depth,
            nodes_visited=result.nodes_visited,
            elapsed_time=result.elapsed_time,
            algorithm=result.algorithm,
            status_after_move=status_after,
        )
        self.history.append(step)
        self.current_player = AI if player == HUMAN else HUMAN
        return step

    def undo_last_step(self) -> AutoPlayStep | None:
        if not self.history:
            return None

        step = self.history.pop()
        if step.move is not None:
            row, col = step.move
            self.board.undo_move(row, col)
        self.current_player = step.player
        return step

    def update_ai_modes(self, x_mode: str, o_mode: str) -> None:
        x_mode = normalize_ai_mode(x_mode)
        o_mode = normalize_ai_mode(o_mode)

        if x_mode != self.x_mode:
            self.x_mode = x_mode
            self.x_ai = create_ai(self.x_mode)
        if o_mode != self.o_mode:
            self.o_mode = o_mode
            self.o_ai = create_ai(self.o_mode)

    def _choose_move(self, player: str) -> SearchResult:
        search_board = self.board.clone()
        if player == AI:
            return self.o_ai.search(search_board, self.depth, ai_player=AI)
        return self.x_ai.search(search_board, self.depth, ai_player=HUMAN)

    @property
    def total_nodes_visited(self) -> int:
        return sum(step.nodes_visited for step in self.history)

    @property
    def total_elapsed_time(self) -> float:
        return sum(step.elapsed_time for step in self.history)

    def clone_branch(self, swap_algorithms: bool = False, additional_turns: int | None = None) -> "AutoPlayGame":
        x_mode = self.o_mode if swap_algorithms else self.x_mode
        o_mode = self.x_mode if swap_algorithms else self.o_mode
        max_turns = self.max_turns
        if additional_turns is not None:
            max_turns = len(self.history) + additional_turns

        branch = AutoPlayGame(
            size=self.board.size,
            x_mode=x_mode,
            o_mode=o_mode,
            depth=self.depth,
            max_turns=max_turns,
        )
        branch.board = self.board.clone()
        branch.history = list(self.history)
        branch.current_player = self.current_player
        return branch
