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
from engine.ai_runner import AI_MODE_OPTIONS, base_algorithm, create_ai, normalize_ai_mode
from engine.auto_play import AutoPlayGame, AutoPlayStep
from engine.game_engine import GameEngine


RESULT_PATH = Path(__file__).resolve().parents[1] / "results" / "benchmark_results.csv"
SESSION_DIR = Path(__file__).resolve().parents[1] / "results" / "sessions"

APP_BG = "#eef2f7"
PANEL_BG = "#ffffff"
TEXT_BG = "#f8fafc"
GRID_LINE = "#d1d5db"
X_BG = "#dbeafe"
X_FG = "#1d4ed8"
O_BG = "#fee2e2"
O_FG = "#b91c1c"
EMPTY_BG = "#f9fafb"


def format_autoplay_step(step: AutoPlayStep) -> str:
    return (
        f"Turn {step.turn:02d} | Player {step.player} | {step.algorithm} | "
        f"move={step.move} | score={step.score} | depth={step.depth} | "
        f"nodes={step.nodes_visited} | time={step.elapsed_time:.6f}s"
    )


class BoardView(ttk.Frame):
    def __init__(self, master, on_cell_click=None, cell_width: int = 4, cell_height: int = 2, font_size: int = 11):
        super().__init__(master)
        self.configure(style="Surface.TFrame")
        self.on_cell_click = on_cell_click
        self.cell_width = cell_width
        self.cell_height = cell_height
        self.font_size = font_size
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
                    width=self.cell_width,
                    height=self.cell_height,
                    font=("Segoe UI", self.font_size, "bold"),
                    relief=tk.FLAT,
                    bd=0,
                    highlightthickness=1,
                    highlightbackground=GRID_LINE,
                    activebackground="#e0f2fe",
                    cursor="hand2",
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
                color = EMPTY_BG
                foreground = "#111827"
                if value == HUMAN:
                    color = X_BG
                    foreground = X_FG
                elif value == AI:
                    color = O_BG
                    foreground = O_FG

                self.buttons[row][col].configure(text=text, bg=color, fg=foreground)

    def _handle_click(self, row: int, col: int) -> None:
        if self.interactive and self.on_cell_click is not None:
            self.on_cell_click(row, col)


class AutoPlaySessionPane(ttk.LabelFrame):
    def __init__(self, master, title: str):
        super().__init__(master, text=title, padding=10, style="Panel.TLabelframe")
        self.status_var = tk.StringVar(value="No session.")

        self.board_view = BoardView(self, cell_width=3, cell_height=1, font_size=10)
        self.board_view.pack(anchor=tk.NW)

        ttk.Label(self, textvariable=self.status_var, wraplength=430, style="PanelMuted.TLabel").pack(anchor=tk.W, pady=(8, 4))
        self.log = tk.Text(
            self,
            width=58,
            height=10,
            state=tk.DISABLED,
            bg=TEXT_BG,
            fg="#111827",
            insertbackground="#111827",
            relief=tk.FLAT,
            padx=10,
            pady=8,
            font=("Consolas", 9),
        )
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
        self.mode_var = tk.StringVar(value="4 - alphabeta-improve")
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
            width=22,
            textvariable=self.mode_var,
            values=AI_MODE_OPTIONS,
            state="readonly",
        ).grid(row=0, column=3, padx=(6, 16))

        ttk.Label(controls, text="Depth").grid(row=0, column=4, sticky=tk.W)
        ttk.Spinbox(controls, from_=1, to=8, width=6, textvariable=self.depth_var).grid(
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
        self.log = tk.Text(
            side_panel,
            width=56,
            height=22,
            state=tk.DISABLED,
            bg=TEXT_BG,
            fg="#111827",
            relief=tk.FLAT,
            padx=10,
            pady=8,
            font=("Consolas", 9),
        )
        self.log.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

    def new_game(self) -> None:
        try:
            size = self._read_int(self.size_var, minimum=9)
            depth = self._read_int(self.depth_var, minimum=1, maximum=8)
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

    def _read_int(self, var: tk.StringVar, minimum: int, maximum: int | None = None) -> int:
        try:
            value = int(var.get())
        except ValueError as exc:
            raise ValueError("Please enter a valid integer.") from exc
        if value < minimum:
            raise ValueError(f"Value must be at least {minimum}.")
        if maximum is not None and value > maximum:
            raise ValueError(f"Value must be at most {maximum}.")
        return value

    def _mode_from_var(self, var: tk.StringVar) -> str:
        return normalize_ai_mode(var.get().split()[0])

    def _settings_from_controls(self) -> tuple[int, str, int]:
        size = self._read_int(self.size_var, minimum=9)
        depth = self._read_int(self.depth_var, minimum=1, maximum=8)
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
        self.cutoff_var = tk.StringVar(value="Alpha-Beta cut-off nodes: 0")
        self.x_mode_var = tk.StringVar(value="3 - minimax-improve")
        self.o_mode_var = tk.StringVar(value="4 - alphabeta-improve")
        self.status_var = tk.StringVar(value="Create a new AI vs AI game to start.")
        self.alpha_beta_cutoff_total = 0
        self.cutoff_lines: list[str] = []
        self.cutoff_comparison_enabled = False

        self._build_layout()
        self.new_game()

    def _build_layout(self) -> None:
        controls = ttk.Frame(self, style="Surface.TFrame")
        controls.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(controls, text="Board size").grid(row=0, column=0, sticky=tk.W)
        ttk.Spinbox(controls, from_=9, to=25, width=6, textvariable=self.size_var).grid(
            row=0, column=1, padx=(6, 14)
        )

        ttk.Label(controls, text="X AI").grid(row=0, column=2, sticky=tk.W)
        self.x_mode_combo = ttk.Combobox(
            controls,
            width=22,
            textvariable=self.x_mode_var,
            values=AI_MODE_OPTIONS,
            state="readonly",
        )
        self.x_mode_combo.grid(row=0, column=3, padx=(6, 14))
        self.x_mode_combo.bind("<<ComboboxSelected>>", self._refresh_branch_ui_from_controls)

        ttk.Label(controls, text="O AI").grid(row=0, column=4, sticky=tk.W)
        self.o_mode_combo = ttk.Combobox(
            controls,
            width=22,
            textvariable=self.o_mode_var,
            values=AI_MODE_OPTIONS,
            state="readonly",
        )
        self.o_mode_combo.grid(row=0, column=5, padx=(6, 14))
        self.o_mode_combo.bind("<<ComboboxSelected>>", self._refresh_branch_ui_from_controls)

        ttk.Label(controls, text="Depth").grid(row=1, column=0, sticky=tk.W, pady=(8, 0))
        ttk.Spinbox(controls, from_=1, to=8, width=6, textvariable=self.depth_var).grid(
            row=1, column=1, padx=(6, 14), pady=(8, 0)
        )

        ttk.Label(controls, text="Max turns").grid(row=1, column=2, sticky=tk.W, pady=(8, 0))
        ttk.Spinbox(controls, from_=1, to=625, width=8, textvariable=self.max_turns_var).grid(
            row=1, column=3, padx=(6, 14), pady=(8, 0)
        )

        ttk.Label(controls, text="Next moves after swap").grid(row=1, column=4, sticky=tk.W, pady=(8, 0))
        ttk.Spinbox(controls, from_=1, to=200, width=7, textvariable=self.branch_moves_var).grid(
            row=1, column=5, padx=(6, 14), pady=(8, 0)
        )

        ttk.Button(controls, text="New game", command=self.new_game, style="Accent.TButton").grid(row=2, column=0, pady=(10, 0))
        ttk.Button(controls, text="Step", command=self.step_once).grid(row=2, column=1, pady=(8, 0))
        self.run_button = ttk.Button(controls, text="Run all", command=self.toggle_run)
        self.run_button.grid(row=2, column=2, padx=(8, 0), pady=(8, 0))
        ttk.Button(controls, text="Pause", command=self.pause).grid(row=2, column=3, padx=(8, 0), pady=(8, 0))
        ttk.Button(controls, text="Resume", command=self.resume).grid(row=2, column=4, padx=(8, 0), pady=(8, 0))
        self.swap_button = ttk.Button(controls, text="Swap roles", command=self.swap_roles)
        self.swap_button.grid(
            row=2, column=5, padx=(8, 0), pady=(8, 0)
        )
        ttk.Button(controls, text="Save state", command=self.save_current_state).grid(
            row=2, column=6, padx=(8, 0), pady=(8, 0)
        )
        self.cutoff_label = ttk.Label(controls, textvariable=self.cutoff_var, style="Metric.TLabel")
        self.cutoff_label.grid(
            row=3, column=0, columnspan=7, padx=(0, 0), pady=(10, 0), sticky=tk.W
        )

        self.cutoff_container = ttk.Frame(self, style="Surface.TFrame")
        self.cutoff_panel = ttk.LabelFrame(
            self.cutoff_container,
            text="Alpha-Beta cut-off by turn",
            padding=8,
            style="Panel.TLabelframe",
        )
        self.cutoff_panel.pack(fill=tk.X)
        self.cutoff_log = tk.Text(
            self.cutoff_panel,
            height=4,
            state=tk.DISABLED,
            bg=TEXT_BG,
            fg="#0f172a",
            relief=tk.FLAT,
            padx=10,
            pady=6,
            font=("Consolas", 9),
        )
        self.cutoff_log.pack(fill=tk.X, expand=True)

        self.status_label = ttk.Label(self, textvariable=self.status_var, wraplength=980, style="Muted.TLabel")
        self.status_label.pack(anchor=tk.W, pady=(0, 8))

        self.body = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.body.pack(fill=tk.BOTH, expand=True)

        self.original_pane = AutoPlaySessionPane(self.body, "Current / original roles")
        self.swapped_pane = AutoPlaySessionPane(self.body, "Swapped roles branch")
        self.body.add(self.original_pane, weight=1)
        self.body.add(self.swapped_pane, weight=1)
        self._set_cutoff_visibility(False)

    def new_game(self) -> None:
        if self.busy:
            return

        try:
            size = self._read_int(self.size_var, minimum=9)
            depth = self._read_int(self.depth_var, minimum=1, maximum=8)
            max_turns = self._read_int(self.max_turns_var, minimum=1)
            x_mode = self._mode_from_var(self.x_mode_var)
            o_mode = self._mode_from_var(self.o_mode_var)
        except ValueError as exc:
            messagebox.showerror("Invalid input", str(exc))
            return

        self.running = False
        self.branch_running = False
        self.run_button.configure(text="Run all")
        self.alpha_beta_cutoff_total = 0
        self.cutoff_lines = []
        self.cutoff_var.set("Alpha-Beta cut-off nodes: 0")
        self._clear_cutoff_log()
        self._set_branch_controls_visibility(self._should_enable_swap_for_modes(x_mode, o_mode))
        self._set_cutoff_visibility(self._should_show_cutoff_for_modes(x_mode, o_mode))
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
        self.swapped_pane.status_var.set("Use Swap roles to create this branch.")
        if self._should_enable_swap_for_modes(x_mode, o_mode):
            self.status_var.set("Ready. Use Step, Run all, Pause, Resume, or Swap roles.")
        else:
            self.status_var.set("Ready. Same AI mode on both sides, so Swap roles is hidden.")

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
        self._start_main_step(keep_running=True)

    def pause(self) -> None:
        self.running = False
        self.branch_running = False
        self.run_button.configure(text="Run all")
        self.status_var.set("Paused.")
        if self.branch_games is not None:
            self._save_branch_outputs()

    def resume(self) -> None:
        if self.busy:
            return

        if self.branch_games is not None:
            if not self._has_branch_move_left():
                self._extend_branch_limits()
            if self._has_branch_move_left():
                self.branch_running = True
                self._start_branch_step(keep_running=True)
            return

        if self.game is None:
            return

        if self.game.status() == "ONGOING" and len(self.game.history) >= self.game.max_turns:
            try:
                self.game.max_turns += self._read_int(self.branch_moves_var, minimum=1)
            except ValueError as exc:
                messagebox.showerror("Invalid input", str(exc))
                return

        if self.game.status() == "ONGOING":
            self.running = True
            self._start_main_step(keep_running=True)

    def swap_roles(self) -> None:
        if self.game is None or self.busy:
            return

        self.pause()
        if not self._ensure_current_settings():
            return
        if self.game.status() != "ONGOING":
            self.status_var.set(f"Cannot swap: game status is {self.game.status()}.")
            return
        if not self._should_enable_swap_for_modes(self.game.x_mode, self.game.o_mode):
            self.status_var.set("Swap roles is hidden because both AI players use the same mode.")
            self._set_branch_controls_visibility(False)
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
        self.alpha_beta_cutoff_total = 0
        self.cutoff_lines = []
        self.cutoff_var.set("Alpha-Beta cut-off nodes: 0")
        self._clear_cutoff_log()
        self._set_cutoff_visibility(self._should_show_cutoff_for_modes(original.x_mode, original.o_mode))
        self.session_dir = self._save_swap_snapshot(original, swapped)
        self.status_var.set(
            f"Swap created. Each branch will play at most {additional_turns} more moves. "
            f"Snapshot saved to {self.session_dir}"
        )
        self.branch_running = True
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
            self.run_button.configure(text="Run all")
            self.status_var.set("Both branches reached the current move limit. Use Resume to extend them.")
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
        self._update_cutoff_from_updates(updates)
        if keep_running and self.branch_running and self._has_branch_move_left():
            self.after(80, lambda: self._start_branch_step(keep_running=True))
            return

        self.branch_running = False
        self.run_button.configure(text="Run all")
        final_text = "Paused." if self._has_branch_move_left() else "Both branches reached the current move limit."
        self.status_var.set(final_text)
        self._save_branch_outputs()

    def _has_branch_move_left(self) -> bool:
        if self.branch_games is None:
            return False
        return any(game.status() == "ONGOING" and len(game.history) < game.max_turns for game in self.branch_games.values())

    def _extend_branch_limits(self) -> None:
        if self.branch_games is None:
            return
        try:
            additional_turns = self._read_int(self.branch_moves_var, minimum=1)
        except ValueError as exc:
            messagebox.showerror("Invalid input", str(exc))
            return

        for game in self.branch_games.values():
            if game.status() == "ONGOING":
                game.max_turns = len(game.history) + additional_turns
        self.branch_status_logged = set()
        self.status_var.set(f"Resume added {additional_turns} more moves to unfinished branches.")

    def _update_cutoff_from_updates(self, updates) -> None:
        if not self.cutoff_comparison_enabled:
            return

        steps = [step for _, step, _, _ in updates if step is not None]
        if len(steps) != 2:
            return

        minimax_step = next((step for step in steps if step.algorithm.startswith("Minimax")), None)
        alphabeta_step = next((step for step in steps if step.algorithm.startswith("Alpha-Beta")), None)
        if minimax_step is None or alphabeta_step is None:
            return

        cut_off = max(0, minimax_step.nodes_visited - alphabeta_step.nodes_visited)
        self.alpha_beta_cutoff_total += cut_off
        turn = max(minimax_step.turn, alphabeta_step.turn)
        line = (
            f"Turn {turn:02d} | {alphabeta_step.algorithm}'s nodes: {alphabeta_step.nodes_visited} | "
            f"{minimax_step.algorithm}'s nodes={minimax_step.nodes_visited} | "
            f"Nodes cut off={cut_off}"
        )
        self.cutoff_lines.append(line)
        self._append_cutoff_log(line)
        self.cutoff_var.set(f"Alpha-Beta cut-off nodes: {self.alpha_beta_cutoff_total}")

    def _should_show_cutoff_for_modes(self, x_mode: str, o_mode: str) -> bool:
        return {base_algorithm(x_mode), base_algorithm(o_mode)} == {"minimax", "alphabeta"}

    def _should_enable_swap_for_modes(self, x_mode: str, o_mode: str) -> bool:
        return normalize_ai_mode(x_mode) != normalize_ai_mode(o_mode)

    def _refresh_branch_ui_from_controls(self, *_args) -> None:
        try:
            x_mode = self._mode_from_var(self.x_mode_var)
            o_mode = self._mode_from_var(self.o_mode_var)
        except ValueError:
            return

        self._set_branch_controls_visibility(self._should_enable_swap_for_modes(x_mode, o_mode))

    def _set_branch_controls_visibility(self, visible: bool) -> None:
        if visible:
            self.swap_button.grid()
            self._set_swapped_pane_visibility(True)
            return

        self.swap_button.grid_remove()
        if self.branch_games is None:
            self._set_swapped_pane_visibility(False)

    def _set_swapped_pane_visibility(self, visible: bool) -> None:
        pane_id = str(self.swapped_pane)
        pane_ids = set(self.body.panes())
        if visible and pane_id not in pane_ids:
            self.body.add(self.swapped_pane, weight=1)
            return
        if not visible and pane_id in pane_ids:
            self.body.forget(self.swapped_pane)

    def _set_cutoff_visibility(self, visible: bool) -> None:
        self.cutoff_comparison_enabled = visible
        if visible:
            self.cutoff_label.grid()
            if not self.cutoff_container.winfo_manager():
                self.cutoff_container.pack(fill=tk.X, pady=(0, 8), before=self.status_label)
            return

        self.cutoff_label.grid_remove()
        if self.cutoff_container.winfo_manager():
            self.cutoff_container.pack_forget()

    def _append_cutoff_log(self, message: str) -> None:
        self.cutoff_log.configure(state=tk.NORMAL)
        self.cutoff_log.insert(tk.END, message + "\n")
        self.cutoff_log.see(tk.END)
        self.cutoff_log.configure(state=tk.DISABLED)

    def _clear_cutoff_log(self) -> None:
        self.cutoff_log.configure(state=tk.NORMAL)
        self.cutoff_log.delete("1.0", tk.END)
        self.cutoff_log.configure(state=tk.DISABLED)

    def _effective_status(self, game: AutoPlayGame) -> str:
        status = game.status()
        if status == "ONGOING" and len(game.history) >= game.max_turns:
            return "MAX_TURNS_REACHED"
        return status

    def _save_swap_snapshot(self, original: AutoPlayGame, swapped: AutoPlayGame) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = SESSION_DIR / f"swap_{timestamp}"
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
                    f"alpha_beta_cutoff_nodes={self.alpha_beta_cutoff_total}",
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
        if self.cutoff_comparison_enabled:
            (self.session_dir / "cutoff_summary.txt").write_text(
                "\n".join(
                    [
                        f"alpha_beta_cutoff_nodes_total={self.alpha_beta_cutoff_total}",
                        *self.cutoff_lines,
                    ]
                ),
                encoding="utf-8",
            )

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

    def _read_int(self, var: tk.StringVar, minimum: int, maximum: int | None = None) -> int:
        try:
            value = int(var.get())
        except ValueError as exc:
            raise ValueError("Please enter a valid integer.") from exc
        if value < minimum:
            raise ValueError(f"Value must be at least {minimum}.")
        if maximum is not None and value > maximum:
            raise ValueError(f"Value must be at most {maximum}.")
        return value

    def _mode_from_var(self, var: tk.StringVar) -> str:
        return normalize_ai_mode(var.get().split()[0])

    def _settings_from_controls(self) -> tuple[int, str, str, int, int]:
        size = self._read_int(self.size_var, minimum=9)
        depth = self._read_int(self.depth_var, minimum=1, maximum=8)
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
        self.table.column("algorithm", width=170, anchor=tk.CENTER)
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
                for mode in ("minimax", "alphabeta", "minimax-improve", "alphabeta-improve"):
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
        self.geometry("1280x820")
        self.minsize(1100, 700)
        self.configure(bg=APP_BG)
        self._configure_style()

        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=14, pady=14)

        notebook.add(HumanVsAIFrame(notebook), text="Human vs AI")
        notebook.add(AIVsAIFrame(notebook), text="AI vs AI")
        notebook.add(BenchmarkFrame(notebook), text="Benchmark")

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        style.configure(".", font=("Segoe UI", 10), background=APP_BG, foreground="#111827")
        style.configure("TFrame", background=APP_BG)
        style.configure("Surface.TFrame", background=PANEL_BG)
        style.configure("TLabel", background=APP_BG, foreground="#111827")
        style.configure("Muted.TLabel", background=APP_BG, foreground="#475569")
        style.configure("PanelMuted.TLabel", background=PANEL_BG, foreground="#475569")
        style.configure("Metric.TLabel", background=APP_BG, foreground="#0f766e", font=("Segoe UI", 10, "bold"))
        style.configure("TButton", padding=(12, 7), relief="flat", background="#e5e7eb")
        style.map(
            "TButton",
            background=[("active", "#d1d5db"), ("pressed", "#cbd5e1")],
        )
        style.configure("Accent.TButton", padding=(14, 8), background="#2563eb", foreground="#ffffff")
        style.map(
            "Accent.TButton",
            background=[("active", "#1d4ed8"), ("pressed", "#1e40af")],
            foreground=[("active", "#ffffff")],
        )
        style.configure("TNotebook", background=APP_BG, borderwidth=0)
        style.configure("TNotebook.Tab", padding=(14, 8), background="#e5e7eb")
        style.map("TNotebook.Tab", background=[("selected", PANEL_BG), ("active", "#f8fafc")])
        style.configure("Panel.TLabelframe", background=PANEL_BG, bordercolor="#d1d5db", relief="solid")
        style.configure("Panel.TLabelframe.Label", background=PANEL_BG, foreground="#0f172a", font=("Segoe UI", 10, "bold"))
        style.configure("Treeview", background=TEXT_BG, fieldbackground=TEXT_BG, rowheight=26, borderwidth=0)
        style.configure("Treeview.Heading", background="#e2e8f0", foreground="#0f172a", font=("Segoe UI", 10, "bold"))


def run_gui() -> None:
    app = CaroApp()
    app.mainloop()
