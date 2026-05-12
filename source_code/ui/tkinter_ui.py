from __future__ import annotations

import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk

from benchmark.result_writer import write_results_csv
from benchmark.test_states import TEST_STATES
from core.board import Board
from core.constants import AI, EMPTY, HUMAN
from engine.ai_runner import create_ai, normalize_ai_mode
from engine.auto_play import AutoPlayGame, AutoPlayStep
from engine.game_engine import GameEngine


RESULT_PATH = Path(__file__).resolve().parents[1] / "results" / "benchmark_results.csv"
SESSION_DIR = Path(__file__).resolve().parents[1] / "results" / "sessions"


def format_autoplay_step(step: AutoPlayStep) -> str:
    return (
        f"Turn {step.turn:02d} | Player {step.player} | {step.algorithm} | "
        f"move={step.move} | score={step.score} | depth={step.depth} | "
        f"nodes={step.nodes_visited} | time={step.elapsed_time:.6f}s"
    )


class BoardView(ttk.Frame):
    def __init__(self, master, on_cell_click=None):
        super().__init__(master)
        self.on_cell_click = on_cell_click
        self.buttons: list[list[tk.Button]] = []
        self.interactive = False

    def build(self, size: int) -> None:
        for child in self.winfo_children():
            child.destroy()

        self.buttons = []
        for row in range(size):
            button_row = []
            for col in range(size):
                button = tk.Button(
                    self,
                    text="",
                    width=3,
                    height=1,
                    font=("Segoe UI", 11, "bold"),
                    relief=tk.RIDGE,
                    command=lambda r=row, c=col: self._handle_click(r, c),
                )
                button.grid(row=row, column=col, padx=1, pady=1)
                button_row.append(button)
            self.buttons.append(button_row)

    def set_interactive(self, enabled: bool) -> None:
        self.interactive = enabled

    def refresh_board(self, board: Board) -> None:
        self.refresh_grid(board.grid)

    def refresh_grid(self, grid: list[list[str]]) -> None:
        for row, values in enumerate(grid):
            for col, value in enumerate(values):
                text = "" if value == EMPTY else value
                color = "#f8fafc"
                foreground = "#111827"
                if value == HUMAN:
                    color = "#dbeafe"
                    foreground = "#1d4ed8"
                elif value == AI:
                    color = "#fee2e2"
                    foreground = "#b91c1c"

                self.buttons[row][col].configure(text=text, bg=color, fg=foreground)

    def _handle_click(self, row: int, col: int) -> None:
        if self.interactive and self.on_cell_click is not None:
            self.on_cell_click(row, col)


class AutoPlaySessionPane(ttk.LabelFrame):
    def __init__(self, master, title: str):
        super().__init__(master, text=title, padding=8)
        self.status_var = tk.StringVar(value="No session.")

        self.board_view = BoardView(self)
        self.board_view.pack(anchor=tk.NW)

        ttk.Label(self, textvariable=self.status_var, wraplength=430).pack(anchor=tk.W, pady=(8, 4))
        self.log = tk.Text(self, width=58, height=15, state=tk.DISABLED)
        self.log.pack(fill=tk.BOTH, expand=True)

    def build(self, size: int) -> None:
        self.board_view.build(size)

    def refresh_game(self, game: AutoPlayGame) -> None:
        self.board_view.refresh_board(game.board)
        self.status_var.set(self._status_text(game))

    def refresh_grid(self, grid: list[list[str]], game: AutoPlayGame) -> None:
        self.board_view.refresh_grid(grid)
        self.status_var.set(self._status_text(game))

    def clear_log(self) -> None:
        self.log.configure(state=tk.NORMAL)
        self.log.delete("1.0", tk.END)
        self.log.configure(state=tk.DISABLED)

    def append_log(self, message: str) -> None:
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, message + "\n")
        self.log.see(tk.END)
        self.log.configure(state=tk.DISABLED)

    def load_history(self, game: AutoPlayGame, title: str) -> None:
        self.configure(text=title)
        self.clear_log()
        self.append_log(
            f"Session start | X={game.x_mode} | O={game.o_mode} | "
            f"depth={game.depth} | inherited_turns={len(game.history)} | "
            f"inherited_nodes={game.total_nodes_visited} | "
            f"inherited_time={game.total_elapsed_time:.6f}s | next={game.current_player}"
        )
        for step in game.history:
            self.append_log(format_autoplay_step(step))
        self.refresh_game(game)

    def _status_text(self, game: AutoPlayGame) -> str:
        remaining = max(0, game.max_turns - len(game.history))
        return (
            f"Status={game.status()} | next={game.current_player} | "
            f"turns={len(game.history)}/{game.max_turns} | remaining={remaining} | "
            f"total_nodes={game.total_nodes_visited}"
        )


class HumanVsAIFrame(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=12)
        self.game: GameEngine | None = None
        self.game_settings: tuple[int, str, int] | None = None
        self.busy = False

        self.size_var = tk.StringVar(value="9")
        self.depth_var = tk.StringVar(value="2")
        self.mode_var = tk.StringVar(value="2 - alphabeta")
        self.status_var = tk.StringVar(value="Create a new game to start.")

        self._build_layout()
        self.new_game()

    def _build_layout(self) -> None:
        controls = ttk.Frame(self)
        controls.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(controls, text="Board size").grid(row=0, column=0, sticky=tk.W)
        ttk.Spinbox(controls, from_=9, to=25, width=6, textvariable=self.size_var).grid(
            row=0, column=1, padx=(6, 16)
        )

        ttk.Label(controls, text="AI mode").grid(row=0, column=2, sticky=tk.W)
        ttk.Combobox(
            controls,
            width=16,
            textvariable=self.mode_var,
            values=("1 - minimax", "2 - alphabeta"),
            state="readonly",
        ).grid(row=0, column=3, padx=(6, 16))

        ttk.Label(controls, text="Depth").grid(row=0, column=4, sticky=tk.W)
        ttk.Spinbox(controls, from_=1, to=5, width=6, textvariable=self.depth_var).grid(
            row=0, column=5, padx=(6, 16)
        )

        ttk.Button(controls, text="New game", command=self.new_game).grid(row=0, column=6)

        body = ttk.Frame(self)
        body.pack(fill=tk.BOTH, expand=True)

        self.board_view = BoardView(body, on_cell_click=self.on_cell_click)
        self.board_view.pack(side=tk.LEFT, anchor=tk.N)

        side_panel = ttk.Frame(body, padding=(14, 0, 0, 0))
        side_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        ttk.Label(side_panel, textvariable=self.status_var, wraplength=360).pack(anchor=tk.W)
        self.log = tk.Text(side_panel, width=56, height=22, state=tk.DISABLED)
        self.log.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

    def new_game(self) -> None:
        try:
            size = self._read_int(self.size_var, minimum=9)
            depth = self._read_int(self.depth_var, minimum=1)
            mode = self._mode_from_var(self.mode_var)
        except ValueError as exc:
            messagebox.showerror("Invalid input", str(exc))
            return

        self.game = GameEngine(size=size, ai_mode=mode, depth=depth)
        self.game_settings = (size, mode, depth)
        self.board_view.build(size)
        self.board_view.refresh_board(self.game.board)
        self.board_view.set_interactive(True)
        self.busy = False
        self.status_var.set("Your turn. Click an empty cell to place X.")
        self._clear_log()
        self._append_log(f"New Human vs AI game. AI mode={mode}, depth={depth}.")

    def on_cell_click(self, row: int, col: int) -> None:
        if self.game is None or self.busy:
            return

        if not self._ensure_current_settings():
            return

        if self.game.status() != "ONGOING":
            return

        if not self.game.human_move(row, col):
            self.status_var.set("Invalid move. Choose an empty cell inside the board.")
            return

        self.board_view.refresh_board(self.game.board)
        self._append_log(f"Human X moved to ({row}, {col}).")

        status = self.game.status()
        if status != "ONGOING":
            self._finish_game(status)
            return

        self.busy = True
        self.board_view.set_interactive(False)
        self.status_var.set("AI is thinking...")
        threading.Thread(target=self._run_ai_move, daemon=True).start()

    def _run_ai_move(self) -> None:
        assert self.game is not None
        result = self.game.ai_move()
        grid = [row[:] for row in self.game.board.grid]
        status = self.game.status()
        self.after(0, self._finish_ai_move, result, grid, status)

    def _finish_ai_move(self, result, grid: list[list[str]], status: str) -> None:
        self.board_view.refresh_grid(grid)
        self._append_log(
            f"AI {result.player} | {result.algorithm} | move={result.best_move} | "
            f"score={result.score} | depth={result.depth} | "
            f"nodes={result.nodes_visited} | time={result.elapsed_time:.6f}s"
        )
        self.busy = False
        self.board_view.set_interactive(status == "ONGOING")

        if status == "ONGOING":
            self.status_var.set("Your turn. Click an empty cell to place X.")
        else:
            self._finish_game(status)

    def _finish_game(self, status: str) -> None:
        self.board_view.set_interactive(False)
        label = {
            "HUMAN_WIN": "Human X wins.",
            "AI_WIN": "AI O wins.",
            "DRAW": "Draw.",
        }.get(status, status)
        self.status_var.set(f"Game over: {label}")
        self._append_log(f"Game over: {label}")

    def _append_log(self, message: str) -> None:
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, message + "\n")
        self.log.see(tk.END)
        self.log.configure(state=tk.DISABLED)

    def _clear_log(self) -> None:
        self.log.configure(state=tk.NORMAL)
        self.log.delete("1.0", tk.END)
        self.log.configure(state=tk.DISABLED)

    def _read_int(self, var: tk.StringVar, minimum: int) -> int:
        try:
            value = int(var.get())
        except ValueError as exc:
            raise ValueError("Please enter a valid integer.") from exc
        if value < minimum:
            raise ValueError(f"Value must be at least {minimum}.")
        return value

    def _mode_from_var(self, var: tk.StringVar) -> str:
        return normalize_ai_mode(var.get().split()[0])

    def _settings_from_controls(self) -> tuple[int, str, int]:
        size = self._read_int(self.size_var, minimum=9)
        depth = self._read_int(self.depth_var, minimum=1)
        mode = self._mode_from_var(self.mode_var)
        return size, mode, depth

    def _ensure_current_settings(self) -> bool:
        try:
            settings = self._settings_from_controls()
        except ValueError as exc:
            messagebox.showerror("Invalid input", str(exc))
            return False

        if settings == self.game_settings:
            return True

        if self.game is not None and not self.game.board.get_occupied_cells():
            self.new_game()
            return True

        self.status_var.set("Settings changed. Press New game to apply them.")
        return False


class AIVsAIFrame(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=12)
        self.game: AutoPlayGame | None = None
        self.branch_games: dict[str, AutoPlayGame] | None = None
        self.game_settings: tuple[int, str, str, int, int] | None = None
        self.session_dir: Path | None = None
        self.branch_status_logged: set[str] = set()
        self.running = False
        self.busy = False
        self.branch_running = False

        self.size_var = tk.StringVar(value="9")
        self.depth_var = tk.StringVar(value="2")
        self.max_turns_var = tk.StringVar(value="81")
        self.branch_moves_var = tk.StringVar(value="4")
        self.x_mode_var = tk.StringVar(value="1 - minimax")
        self.o_mode_var = tk.StringVar(value="2 - alphabeta")
        self.status_var = tk.StringVar(value="Create a new AI vs AI game to start.")

        self._build_layout()
        self.new_game()

    def _build_layout(self) -> None:
        controls = ttk.Frame(self)
        controls.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(controls, text="Board size").grid(row=0, column=0, sticky=tk.W)
        ttk.Spinbox(controls, from_=9, to=25, width=6, textvariable=self.size_var).grid(
            row=0, column=1, padx=(6, 14)
        )

        ttk.Label(controls, text="X AI").grid(row=0, column=2, sticky=tk.W)
        ttk.Combobox(
            controls,
            width=16,
            textvariable=self.x_mode_var,
            values=("1 - minimax", "2 - alphabeta"),
            state="readonly",
        ).grid(row=0, column=3, padx=(6, 14))

        ttk.Label(controls, text="O AI").grid(row=0, column=4, sticky=tk.W)
        ttk.Combobox(
            controls,
            width=16,
            textvariable=self.o_mode_var,
            values=("1 - minimax", "2 - alphabeta"),
            state="readonly",
        ).grid(row=0, column=5, padx=(6, 14))

        ttk.Label(controls, text="Depth").grid(row=1, column=0, sticky=tk.W, pady=(8, 0))
        ttk.Spinbox(controls, from_=1, to=5, width=6, textvariable=self.depth_var).grid(
            row=1, column=1, padx=(6, 14), pady=(8, 0)
        )

        ttk.Label(controls, text="Max turns").grid(row=1, column=2, sticky=tk.W, pady=(8, 0))
        ttk.Spinbox(controls, from_=1, to=625, width=8, textvariable=self.max_turns_var).grid(
            row=1, column=3, padx=(6, 14), pady=(8, 0)
        )

        ttk.Label(controls, text="Next moves after split").grid(row=1, column=4, sticky=tk.W, pady=(8, 0))
        ttk.Spinbox(controls, from_=1, to=200, width=7, textvariable=self.branch_moves_var).grid(
            row=1, column=5, padx=(6, 14), pady=(8, 0)
        )

        ttk.Button(controls, text="New game", command=self.new_game).grid(row=2, column=0, pady=(8, 0))
        ttk.Button(controls, text="Step", command=self.step_once).grid(row=2, column=1, pady=(8, 0))
        self.run_button = ttk.Button(controls, text="Run all", command=self.toggle_run)
        self.run_button.grid(row=2, column=2, padx=(8, 0), pady=(8, 0))
        ttk.Button(controls, text="Pause", command=self.pause).grid(row=2, column=3, padx=(8, 0), pady=(8, 0))
        ttk.Button(controls, text="Split roles", command=self.split_roles).grid(
            row=2, column=4, padx=(8, 0), pady=(8, 0)
        )
        ttk.Button(controls, text="Save state", command=self.save_current_state).grid(
            row=2, column=5, padx=(8, 0), pady=(8, 0)
        )

        ttk.Label(self, textvariable=self.status_var, wraplength=980).pack(anchor=tk.W, pady=(0, 8))

        body = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        body.pack(fill=tk.BOTH, expand=True)

        self.original_pane = AutoPlaySessionPane(body, "Current / original roles")
        self.swapped_pane = AutoPlaySessionPane(body, "Swapped roles branch")
        body.add(self.original_pane, weight=1)
        body.add(self.swapped_pane, weight=1)

    def new_game(self) -> None:
        if self.busy:
            return

        try:
            size = self._read_int(self.size_var, minimum=9)
            depth = self._read_int(self.depth_var, minimum=1)
            max_turns = self._read_int(self.max_turns_var, minimum=1)
            x_mode = self._mode_from_var(self.x_mode_var)
            o_mode = self._mode_from_var(self.o_mode_var)
        except ValueError as exc:
            messagebox.showerror("Invalid input", str(exc))
            return

        self.running = False
        self.branch_running = False
        self.run_button.configure(text="Run all")
        self.game = AutoPlayGame(
            size=size,
            x_mode=x_mode,
            o_mode=o_mode,
            depth=depth,
            max_turns=max_turns,
        )
        self.branch_games = None
        self.branch_status_logged = set()
        self.game_settings = (size, x_mode, o_mode, depth, max_turns)
        self.original_pane.build(size)
        self.swapped_pane.build(size)
        self.original_pane.load_history(self.game, "Current / original roles")
        self.swapped_pane.clear_log()
        self.swapped_pane.configure(text="Swapped roles branch")
        self.swapped_pane.status_var.set("Use Split roles to create this branch.")
        self.status_var.set("Ready. Use Step, Run all, or Split roles.")

    def step_once(self) -> None:
        if self.busy or self.running or self.branch_running:
            return
        if self.branch_games is not None:
            self._start_branch_step(keep_running=False)
            return
        if self.game is None:
            return
        if not self._ensure_current_settings():
            return
        if self.game.status() != "ONGOING":
            self.status_var.set(f"Game over: {self.game.status()}")
            return
        self._start_main_step(keep_running=False)

    def toggle_run(self) -> None:
        if self.branch_games is not None:
            if self.branch_running:
                self.pause()
            else:
                self.branch_running = True
                self.run_button.configure(text="Pause")
                self._start_branch_step(keep_running=True)
            return

        if self.game is None:
            return

        if self.running:
            self.pause()
            return

        if self.busy:
            return

        if not self._ensure_current_settings():
            return

        if self.game.status() != "ONGOING":
            self.status_var.set(f"Game over: {self.game.status()}")
            return

        self.running = True
        self.run_button.configure(text="Pause")
        self._start_main_step(keep_running=True)

    def pause(self) -> None:
        self.running = False
        self.branch_running = False
        self.run_button.configure(text="Run all" if self.branch_games is None else "Resume branches")
        self.status_var.set("Paused.")
        if self.branch_games is not None:
            self._save_branch_outputs()

    def split_roles(self) -> None:
        if self.game is None or self.busy:
            return

        self.pause()
        if not self._ensure_current_settings():
            return
        if self.game.status() != "ONGOING":
            self.status_var.set(f"Cannot split: game status is {self.game.status()}.")
            return

        try:
            additional_turns = self._read_int(self.branch_moves_var, minimum=1)
        except ValueError as exc:
            messagebox.showerror("Invalid input", str(exc))
            return

        original = self.game.clone_branch(swap_algorithms=False, additional_turns=additional_turns)
        swapped = self.game.clone_branch(swap_algorithms=True, additional_turns=additional_turns)
        self.branch_games = {"original": original, "swapped": swapped}
        self.branch_status_logged = set()
        self.original_pane.load_history(original, "Branch A: giữ nguyên vai")
        self.swapped_pane.load_history(swapped, "Branch B: đổi Minimax / Alpha-Beta")
        self.session_dir = self._save_split_snapshot(original, swapped)
        self.status_var.set(
            f"Split created. Each branch will play at most {additional_turns} more moves. "
            f"Snapshot saved to {self.session_dir}"
        )
        self.branch_running = True
        self.run_button.configure(text="Pause")
        self._start_branch_step(keep_running=True)

    def save_current_state(self) -> None:
        if self.branch_games is not None:
            self._save_branch_outputs()
            self.status_var.set(f"Branch states saved to {self.session_dir}")
            return

        if self.game is None:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = SESSION_DIR / f"snapshot_{timestamp}"
        session_dir.mkdir(parents=True, exist_ok=True)
        (session_dir / "board.txt").write_text(self.game.board.to_ascii(), encoding="utf-8")
        (session_dir / "log.txt").write_text(self._history_text(self.game), encoding="utf-8")
        self.status_var.set(f"Current board and log saved to {session_dir}")

    def _start_main_step(self, keep_running: bool) -> None:
        if self.game is None or self.busy:
            return
        if keep_running and not self.running:
            return
        if self.game.status() != "ONGOING" or len(self.game.history) >= self.game.max_turns:
            self.running = False
            self.run_button.configure(text="Run all")
            self.status_var.set(f"Game over: {self._effective_status(self.game)}")
            return

        self.busy = True
        self.status_var.set("Auto play running..." if keep_running else "AI is thinking...")
        threading.Thread(target=self._run_main_step, args=(keep_running,), daemon=True).start()

    def _run_main_step(self, keep_running: bool) -> None:
        assert self.game is not None
        step = self.game.step()
        grid = [row[:] for row in self.game.board.grid]
        status = self._effective_status(self.game)
        self.after(0, self._finish_main_step, step, grid, status, keep_running)

    def _finish_main_step(
        self,
        step: AutoPlayStep | None,
        grid: list[list[str]],
        status: str,
        keep_running: bool,
    ) -> None:
        assert self.game is not None
        self.original_pane.refresh_grid(grid, self.game)
        if step is not None:
            self.original_pane.append_log(format_autoplay_step(step))

        self.busy = False
        if step is None:
            self.running = False
            self.run_button.configure(text="Run all")
            self.status_var.set("Auto play stopped: max turns reached or no legal move.")
            return

        if status == "ONGOING":
            if keep_running and self.running:
                self.status_var.set("Auto play running...")
                self.after(80, lambda: self._start_main_step(keep_running=True))
            else:
                self.status_var.set("Ready for next step.")
        else:
            self.status_var.set(f"Game over: {status}")
            self.original_pane.append_log(f"Game over: {status}")
            self.running = False
            self.run_button.configure(text="Run all")

    def _start_branch_step(self, keep_running: bool) -> None:
        if self.branch_games is None or self.busy:
            return
        if keep_running and not self.branch_running:
            return

        if not self._has_branch_move_left():
            self.branch_running = False
            self.run_button.configure(text="Resume branches")
            self.status_var.set("Both branches are finished.")
            self._save_branch_outputs()
            return

        self.busy = True
        self.status_var.set("Branch sessions running..." if keep_running else "Branch step running...")
        threading.Thread(target=self._run_branch_step, args=(keep_running,), daemon=True).start()

    def _run_branch_step(self, keep_running: bool) -> None:
        assert self.branch_games is not None
        updates = []
        for name, game in self.branch_games.items():
            step = None
            if game.status() == "ONGOING" and len(game.history) < game.max_turns:
                step = game.step()
            updates.append((name, step, [row[:] for row in game.board.grid], self._effective_status(game)))
        self.after(0, self._finish_branch_step, updates, keep_running)

    def _finish_branch_step(self, updates, keep_running: bool) -> None:
        assert self.branch_games is not None
        panes = {"original": self.original_pane, "swapped": self.swapped_pane}
        for name, step, grid, status in updates:
            game = self.branch_games[name]
            pane = panes[name]
            pane.refresh_grid(grid, game)
            if step is not None:
                pane.append_log(f"{format_autoplay_step(step)} | total_nodes={game.total_nodes_visited}")
            if status != "ONGOING" and name not in self.branch_status_logged:
                pane.append_log(f"Session status: {status}")
                self.branch_status_logged.add(name)

        self.busy = False
        if keep_running and self.branch_running and self._has_branch_move_left():
            self.after(80, lambda: self._start_branch_step(keep_running=True))
            return

        self.branch_running = False
        self.run_button.configure(text="Resume branches" if self._has_branch_move_left() else "Run all")
        final_text = "Paused." if self._has_branch_move_left() else "Both branches are finished."
        self.status_var.set(final_text)
        self._save_branch_outputs()

    def _has_branch_move_left(self) -> bool:
        if self.branch_games is None:
            return False
        return any(game.status() == "ONGOING" and len(game.history) < game.max_turns for game in self.branch_games.values())

    def _effective_status(self, game: AutoPlayGame) -> str:
        status = game.status()
        if status == "ONGOING" and len(game.history) >= game.max_turns:
            return "MAX_TURNS_REACHED"
        return status

    def _save_split_snapshot(self, original: AutoPlayGame, swapped: AutoPlayGame) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = SESSION_DIR / f"branch_{timestamp}"
        session_dir.mkdir(parents=True, exist_ok=True)

        base = self.game if self.game is not None else original
        (session_dir / "snapshot_board.txt").write_text(base.board.to_ascii(), encoding="utf-8")
        (session_dir / "snapshot_log.txt").write_text(self._history_text(base), encoding="utf-8")
        (session_dir / "branch_info.txt").write_text(
            "\n".join(
                [
                    f"snapshot_turns={len(base.history)}",
                    f"snapshot_nodes={base.total_nodes_visited}",
                    f"snapshot_time={base.total_elapsed_time:.6f}",
                    f"next_player={base.current_player}",
                    f"original_x_mode={original.x_mode}",
                    f"original_o_mode={original.o_mode}",
                    f"swapped_x_mode={swapped.x_mode}",
                    f"swapped_o_mode={swapped.o_mode}",
                    f"branch_max_turns={original.max_turns}",
                ]
            ),
            encoding="utf-8",
        )
        self._write_game_files(original, session_dir, "original_branch")
        self._write_game_files(swapped, session_dir, "swapped_branch")
        return session_dir

    def _save_branch_outputs(self) -> None:
        if self.session_dir is None or self.branch_games is None:
            return
        self._write_game_files(self.branch_games["original"], self.session_dir, "original_branch")
        self._write_game_files(self.branch_games["swapped"], self.session_dir, "swapped_branch")

    def _write_game_files(self, game: AutoPlayGame, session_dir: Path, prefix: str) -> None:
        (session_dir / f"{prefix}_board.txt").write_text(game.board.to_ascii(), encoding="utf-8")
        (session_dir / f"{prefix}_log.txt").write_text(self._history_text(game), encoding="utf-8")

    def _history_text(self, game: AutoPlayGame) -> str:
        lines = [
            f"X={game.x_mode}",
            f"O={game.o_mode}",
            f"depth={game.depth}",
            f"current_player={game.current_player}",
            f"turns={len(game.history)}",
            f"max_turns={game.max_turns}",
            f"total_nodes={game.total_nodes_visited}",
            f"total_time={game.total_elapsed_time:.6f}",
        ]
        lines.extend(format_autoplay_step(step) for step in game.history)
        return "\n".join(lines)

    def _read_int(self, var: tk.StringVar, minimum: int) -> int:
        try:
            value = int(var.get())
        except ValueError as exc:
            raise ValueError("Please enter a valid integer.") from exc
        if value < minimum:
            raise ValueError(f"Value must be at least {minimum}.")
        return value

    def _mode_from_var(self, var: tk.StringVar) -> str:
        return normalize_ai_mode(var.get().split()[0])

    def _settings_from_controls(self) -> tuple[int, str, str, int, int]:
        size = self._read_int(self.size_var, minimum=9)
        depth = self._read_int(self.depth_var, minimum=1)
        max_turns = self._read_int(self.max_turns_var, minimum=1)
        x_mode = self._mode_from_var(self.x_mode_var)
        o_mode = self._mode_from_var(self.o_mode_var)
        return size, x_mode, o_mode, depth, max_turns

    def _ensure_current_settings(self) -> bool:
        try:
            settings = self._settings_from_controls()
        except ValueError as exc:
            messagebox.showerror("Invalid input", str(exc))
            return False

        if settings == self.game_settings:
            return True

        if self.game is not None and not self.game.history:
            self.new_game()
            return True

        self.status_var.set("Settings changed. Press New game to apply them.")
        return False


class BenchmarkFrame(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=12)
        self.running = False
        self.depths_var = tk.StringVar(value="1,2,3")
        self.status_var = tk.StringVar(value="Ready to run benchmark.")
        self._build_layout()

    def _build_layout(self) -> None:
        controls = ttk.Frame(self)
        controls.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(controls, text="Depths").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(controls, width=16, textvariable=self.depths_var).grid(row=0, column=1, padx=(6, 14))
        ttk.Button(controls, text="Run benchmark", command=self.run_benchmark).grid(row=0, column=2)
        ttk.Label(controls, textvariable=self.status_var).grid(row=0, column=3, padx=(14, 0), sticky=tk.W)

        columns = (
            "state",
            "board_size",
            "depth",
            "algorithm",
            "ai_player",
            "best_move",
            "score",
            "nodes_visited",
            "elapsed_time",
        )
        self.table = ttk.Treeview(self, columns=columns, show="headings", height=22)
        for column in columns:
            self.table.heading(column, text=column)
            self.table.column(column, width=120, anchor=tk.CENTER)
        self.table.column("state", width=190, anchor=tk.W)
        self.table.pack(fill=tk.BOTH, expand=True)

    def run_benchmark(self) -> None:
        if self.running:
            return
        try:
            depths = self._parse_depths()
        except ValueError as exc:
            messagebox.showerror("Invalid depths", str(exc))
            return

        for item in self.table.get_children():
            self.table.delete(item)

        self.running = True
        self.status_var.set("Benchmark running...")
        threading.Thread(target=self._benchmark_worker, args=(depths,), daemon=True).start()

    def _benchmark_worker(self, depths: list[int]) -> None:
        rows = []
        for state_name, state_rows in TEST_STATES.items():
            for depth in depths:
                for mode in ("minimax", "alphabeta"):
                    board = Board.from_strings(state_rows)
                    ai = create_ai(mode=mode, move_mode="nearby", radius=1)
                    result = ai.search(board, depth, ai_player=AI)
                    row = {
                        "state": state_name,
                        "board_size": board.size,
                        "depth": depth,
                        "algorithm": result.algorithm,
                        "ai_player": result.player,
                        "best_move": result.best_move,
                        "score": result.score,
                        "nodes_visited": result.nodes_visited,
                        "elapsed_time": f"{result.elapsed_time:.6f}",
                    }
                    rows.append(row)
                    self.after(0, self._add_result_row, row)

        write_results_csv(rows, str(RESULT_PATH))
        self.after(0, self._finish_benchmark, len(rows))

    def _add_result_row(self, row: dict) -> None:
        self.table.insert(
            "",
            tk.END,
            values=(
                row["state"],
                row["board_size"],
                row["depth"],
                row["algorithm"],
                row["ai_player"],
                row["best_move"],
                row["score"],
                row["nodes_visited"],
                row["elapsed_time"],
            ),
        )

    def _finish_benchmark(self, total_rows: int) -> None:
        self.running = False
        self.status_var.set(f"Saved {total_rows} rows to {RESULT_PATH}")

    def _parse_depths(self) -> list[int]:
        raw_values = [value.strip() for value in self.depths_var.get().split(",")]
        depths: list[int] = []
        for raw_value in raw_values:
            if not raw_value:
                continue
            try:
                depth = int(raw_value)
            except ValueError as exc:
                raise ValueError("Depths must be comma-separated integers.") from exc
            if depth < 1:
                raise ValueError("Depths must be at least 1.")
            depths.append(depth)

        if not depths:
            raise ValueError("Enter at least one depth.")
        return depths


class CaroApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Caro AI")
        self.geometry("1120x760")
        self.minsize(960, 640)

        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True)

        notebook.add(HumanVsAIFrame(notebook), text="Human vs AI")
        notebook.add(AIVsAIFrame(notebook), text="AI vs AI")
        notebook.add(BenchmarkFrame(notebook), text="Benchmark")


def run_gui() -> None:
    app = CaroApp()
    app.mainloop()
