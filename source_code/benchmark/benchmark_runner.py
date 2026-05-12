import sys
from pathlib import Path

# Allow running this file from the project root: python source_code/benchmark/benchmark_runner.py
PROJECT_SOURCE = Path(__file__).resolve().parents[1]
if str(PROJECT_SOURCE) not in sys.path:
    sys.path.insert(0, str(PROJECT_SOURCE))

from core.board import Board
from core.constants import AI
from engine.ai_runner import create_ai
from benchmark.test_states import TEST_STATES
from benchmark.result_writer import write_results_csv


def run_benchmark(depths=(1, 2, 3), output_path="source_code/results/benchmark_results.csv"):
    rows = []

    for state_name, state_rows in TEST_STATES.items():
        for depth in depths:
            for mode in ["minimax", "alphabeta", "minimax-improve", "alphabeta-improve"]:
                board = Board.from_strings(state_rows)
                ai = create_ai(mode=mode, move_mode="nearby", radius=1)
                result = ai.search(board, depth, ai_player=AI)
                rows.append({
                    "state": state_name,
                    "board_size": board.size,
                    "depth": depth,
                    "algorithm": result.algorithm,
                    "ai_player": result.player,
                    "best_move": result.best_move,
                    "score": result.score,
                    "nodes_visited": result.nodes_visited,
                    "elapsed_time": f"{result.elapsed_time:.6f}",
                })
                print(rows[-1])

    write_results_csv(rows, output_path)
    print(f"Saved benchmark result to {output_path}")


if __name__ == "__main__":
    run_benchmark()
