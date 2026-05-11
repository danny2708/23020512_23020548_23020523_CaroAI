from engine.game_engine import GameEngine


def run_console_game():
    print("=== CARO AI: Human X vs AI O ===")
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
