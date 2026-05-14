import sys
from pathlib import Path

# Allow running this file from the project root: python source_code/benchmark/benchmark_runner.py
PROJECT_SOURCE = Path(__file__).resolve().parents[1]
if str(PROJECT_SOURCE) not in sys.path:
    sys.path.insert(0, str(PROJECT_SOURCE))

from benchmark.result_writer import write_csv
from benchmark.test_states import TEST_STATES
from core.board import Board
from core.constants import AI
from engine.ai_runner import create_ai


SUMMARY_FIELDS = [
    "Test_ID",
    "State_Name",
    "Algorithm",
    "Depth_Limit",
    "Best_Move_X",
    "Best_Move_Y",
    "Eval_Score",
    "Total_Visited_Nodes",
    "Execution_Time_ms",
    "Winning_Status_Found",
]

PRUNING_FIELDS = [
    "Test_ID",
    "Depth_Where_Pruned",
    "Alpha_Value",
    "Beta_Value",
    "Nodes_Pruned_Estimate",
    "Timestamp",
]

HEURISTIC_FIELDS = [
    "Test_ID",
    "Evaluated_Move_X",
    "Evaluated_Move_Y",
    "Score_Attack",
    "Score_Defense",
    "Position_Weight",
    "Final_Heuristic_Score",
]


def run_benchmark(
    depths=(1, 2, 3, 4),
    output_dir="source_code/results",
    modes=("minimax", "alphabeta"),
) -> dict[str, object]:
    output_dir = Path(output_dir)
    summary_rows: list[dict] = []
    pruning_rows: list[dict] = []
    heuristic_rows: list[dict] = []

    test_index = 1
    for state_name, state_rows in TEST_STATES.items():
        for depth in depths:
            for mode in modes:
                test_id = f"test_{test_index:03d}"
                test_index += 1

                board = Board.from_strings(state_rows)
                ai = create_ai(mode=mode, move_mode="nearby", radius=1)
                _append_heuristic_rows(test_id, board, ai, heuristic_rows)

                result = ai.search(board, depth, ai_player=AI)
                best_move_x, best_move_y = _move_to_xy(result.best_move)
                row = {
                    "Test_ID": test_id,
                    "State_Name": state_name,
                    "Algorithm": result.algorithm,
                    "Depth_Limit": result.depth,
                    "Best_Move_X": best_move_x,
                    "Best_Move_Y": best_move_y,
                    "Eval_Score": result.score,
                    "Total_Visited_Nodes": result.nodes_visited,
                    "Execution_Time_ms": f"{result.elapsed_time * 1000:.3f}",
                    "Winning_Status_Found": abs(result.score) >= 100_000,
                }
                summary_rows.append(row)
                _append_pruning_rows(test_id, result.pruning_events, pruning_rows)
                print(row)

    paths = {
        "summary": output_dir / "benchmark_summary.csv",
        "pruning": output_dir / "pruning_details.csv",
        "heuristic": output_dir / "eval_heuristic_log.csv",
    }
    write_csv(summary_rows, paths["summary"], SUMMARY_FIELDS)
    write_csv(pruning_rows, paths["pruning"], PRUNING_FIELDS)
    write_csv(heuristic_rows, paths["heuristic"], HEURISTIC_FIELDS)
    print(f"Saved benchmark summary to {paths['summary']}")
    print(f"Saved pruning details to {paths['pruning']}")
    print(f"Saved heuristic log to {paths['heuristic']}")
    return {
        "summary": summary_rows,
        "pruning": pruning_rows,
        "heuristic": heuristic_rows,
        "paths": paths,
    }


def _append_heuristic_rows(test_id: str, board: Board, ai, rows: list[dict]) -> None:
    moves = ai.move_generator.generate(
        board,
        player=AI,
        ai_player=AI,
        depth_remaining=1,
        search_depth=1,
        is_root=True,
    )
    for move in moves:
        row, col = move
        board.place_move(row, col, AI)
        breakdown = ai.evaluator.score_breakdown(board, ai_player=AI, evaluated_move=move)
        board.undo_move(row, col)

        move_x, move_y = _move_to_xy(move)
        rows.append(
            {
                "Test_ID": test_id,
                "Evaluated_Move_X": move_x,
                "Evaluated_Move_Y": move_y,
                "Score_Attack": breakdown["score_attack"],
                "Score_Defense": breakdown["score_defense"],
                "Position_Weight": breakdown["position_weight"],
                "Final_Heuristic_Score": breakdown["final_heuristic_score"],
            }
        )


def _append_pruning_rows(test_id: str, pruning_events: list[dict], rows: list[dict]) -> None:
    for event in pruning_events:
        rows.append(
            {
                "Test_ID": test_id,
                "Depth_Where_Pruned": event["depth_where_pruned"],
                "Alpha_Value": event["alpha"],
                "Beta_Value": event["beta"],
                "Nodes_Pruned_Estimate": event["nodes_pruned_estimate"],
                "Timestamp": event["timestamp"],
            }
        )


def _move_to_xy(move: tuple[int, int] | None) -> tuple[int | str, int | str]:
    if move is None:
        return "", ""
    row, col = move
    return col, row


if __name__ == "__main__":
    run_benchmark()
