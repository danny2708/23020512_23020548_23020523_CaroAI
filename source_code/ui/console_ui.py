from engine.game_engine import GameEngine
from engine.auto_play import AutoPlayGame


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
    size = int(input("Board size, minimum 9 [default 9]: ") or "9")
    mode = input("AI mode: minimax / alphabeta [default alphabeta]: ") or "alphabeta"
    depth = int(input("Search depth [default 2]: ") or "2")

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
            f"AI move: {result.best_move}, score={result.score}, "
            f"depth={result.depth}, nodes={result.nodes_visited}, "
            f"time={result.elapsed_time:.6f}s, algorithm={result.algorithm}"
        )


def run_ai_vs_ai_game():
    print("=== AI X vs AI O ===")
    size = int(input("Board size, minimum 9 [default 9]: ") or "9")
    x_mode = input("X algorithm: minimax / alphabeta [default minimax]: ") or "minimax"
    o_mode = input("O algorithm: minimax / alphabeta [default alphabeta]: ") or "alphabeta"
    depth = int(input("Search depth for both AIs [default 2]: ") or "2")
    max_turns = int(input("Max turns [default board size * board size]: ") or str(size * size))

    game = AutoPlayGame(size=size, x_mode=x_mode, o_mode=o_mode, depth=depth, max_turns=max_turns)
    final_status = game.play(verbose=True)

    print("Game over:", final_status)
    print("Total turns:", len(game.history))
    if game.history:
        total_nodes = sum(step.nodes_visited for step in game.history)
        total_time = sum(step.elapsed_time for step in game.history)
        print(f"Total nodes visited: {total_nodes}")
        print(f"Total search time: {total_time:.6f}s")
