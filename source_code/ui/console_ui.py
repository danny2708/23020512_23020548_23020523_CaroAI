from engine.game_engine import GameEngine
from engine.auto_play import AutoPlayGame
from engine.ai_runner import normalize_ai_mode


def read_int(prompt: str, default: int, minimum: int | None = None) -> int:
    while True:
        raw_value = input(prompt).strip()
        if not raw_value:
            value = default
        else:
            try:
                value = int(raw_value)
            except ValueError:
                print("Invalid number. Please enter an integer.")
                continue

        if minimum is not None and value < minimum:
            print(f"Value must be at least {minimum}.")
            continue
        return value


def read_ai_mode(prompt: str, default: str) -> str:
    while True:
        raw_mode = input(prompt).strip() or default
        try:
            return normalize_ai_mode(raw_mode)
        except ValueError:
            print("Invalid AI mode. Enter 1/minimax or 2/alphabeta.")


def run_console_game():
    print("=== CARO AI ===")
    print("1. Human X vs AI O")
    print("2. AI X vs AI O")
    choice = input("Choose mode [default 1]: ") or "1"

    if choice == "2":
        run_ai_vs_ai_game()
    else:
        run_human_vs_ai_game()


def run_human_vs_ai_game():
    print("=== Human X vs AI O ===")
    size = read_int("Board size, minimum 9 [default 9]: ", default=9, minimum=9)
    mode = read_ai_mode("AI mode: 1=minimax / 2=alphabeta [default 2]: ", default="2")
    depth = read_int("Search depth [default 2]: ", default=2, minimum=1)

    game = GameEngine(size=size, ai_mode=mode, depth=depth)

    while True:
        game.board.print_board()
        status = game.status()
        if status != "ONGOING":
            print("Game over:", status)
            break

        try:
            row, col = map(int, input("Your move row col: ").split())
        except ValueError:
            print("Invalid input. Example: 4 4")
            continue

        if not game.human_move(row, col):
            print("Invalid move. Cell is occupied or out of bounds.")
            continue

        if game.status() != "ONGOING":
            continue

        result = game.ai_move()
        print(
            f"AI {result.player} move: {result.best_move}, score={result.score}, "
            f"depth={result.depth}, nodes={result.nodes_visited}, "
            f"time={result.elapsed_time:.6f}s, algorithm={result.algorithm}"
        )


def run_ai_vs_ai_game():
    print("=== AI X vs AI O ===")
    size = read_int("Board size, minimum 9 [default 9]: ", default=9, minimum=9)
    x_mode = read_ai_mode("X algorithm: 1=minimax / 2=alphabeta [default 1]: ", default="1")
    o_mode = read_ai_mode("O algorithm: 1=minimax / 2=alphabeta [default 2]: ", default="2")
    depth = read_int("Search depth for both AIs [default 2]: ", default=2, minimum=1)
    max_turns = read_int(
        "Max turns [default board size * board size]: ",
        default=size * size,
        minimum=1,
    )

    game = AutoPlayGame(size=size, x_mode=x_mode, o_mode=o_mode, depth=depth, max_turns=max_turns)
    final_status = game.play(verbose=True)

    print("Game over:", final_status)
    print("Total turns:", len(game.history))
    if game.history:
        total_nodes = sum(step.nodes_visited for step in game.history)
        total_time = sum(step.elapsed_time for step in game.history)
        print(f"Total nodes visited: {total_nodes}")
        print(f"Total search time: {total_time:.6f}s")
