import sys
from pathlib import Path

# Allow running this file from the project root: python source_code/benchmark/benchmark_runner.py
PROJECT_SOURCE = Path(__file__).resolve().parents[1]
if str(PROJECT_SOURCE) not in sys.path:
    sys.path.insert(0, str(PROJECT_SOURCE))

from benchmark.result_writer import write_csv
from benchmark.test_states import TEST_STATES
from core.board import Board
from core.constants import AI, TERMINAL_WIN_SCORE
from engine.ai_runner import base_algorithm, create_ai, normalize_ai_mode


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

MOVE_MATCHING_FIELDS = [
    "State_Name",
    "Depth_Limit",
    "Minimax_Test_ID",
    "AlphaBeta_Test_ID",
    "Minimax_Algorithm",
    "AlphaBeta_Algorithm",
    "Minimax_Best_Move_X",
    "Minimax_Best_Move_Y",
    "AlphaBeta_Best_Move_X",
    "AlphaBeta_Best_Move_Y",
    "Same_Move",
    "Minimax_Eval_Score",
    "AlphaBeta_Eval_Score",
    "Same_Eval_Score",
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
    move_matching_rows: list[dict] = []

    test_index = 1
    for state_name, state_rows in TEST_STATES.items():
        for depth in depths:
            comparison_results: dict[str, tuple[str, object, dict]] = {}
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
                    "Winning_Status_Found": abs(result.score) >= TERMINAL_WIN_SCORE,
                }
                summary_rows.append(row)
                _append_pruning_rows(test_id, result.pruning_events, pruning_rows)
                comparison_key = base_algorithm(normalize_ai_mode(mode))
                comparison_results.setdefault(comparison_key, (test_id, result, row))
                print(row)
            _append_move_matching_row(state_name, depth, comparison_results, move_matching_rows)

    paths = {
        "summary": output_dir / "benchmark_summary.csv",
        "pruning": output_dir / "pruning_details.csv",
        "heuristic": output_dir / "eval_heuristic_log.csv",
        "move_matching": output_dir / "move_matching.csv",
    }
    write_csv(summary_rows, paths["summary"], SUMMARY_FIELDS)
    write_csv(pruning_rows, paths["pruning"], PRUNING_FIELDS)
    write_csv(heuristic_rows, paths["heuristic"], HEURISTIC_FIELDS)
    write_csv(move_matching_rows, paths["move_matching"], MOVE_MATCHING_FIELDS)
    print(f"Saved benchmark summary to {paths['summary']}")
    print(f"Saved pruning details to {paths['pruning']}")
    print(f"Saved heuristic log to {paths['heuristic']}")
    print(f"Saved move matching report to {paths['move_matching']}")
    return {
        "summary": summary_rows,
        "pruning": pruning_rows,
        "heuristic": heuristic_rows,
        "move_matching": move_matching_rows,
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
        breakdown = ai.evaluator.score_breakdown(board, ai_player=AI, evaluated_move=move)

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


def _append_move_matching_row(
    state_name: str,
    depth: int,
    comparison_results: dict[str, tuple[str, object, dict]],
    rows: list[dict],
) -> None:
    minimax_entry = comparison_results.get("minimax")
    alphabeta_entry = comparison_results.get("alphabeta")
    if minimax_entry is None or alphabeta_entry is None:
        return

    minimax_test_id, minimax_result, minimax_row = minimax_entry
    alphabeta_test_id, alphabeta_result, alphabeta_row = alphabeta_entry
    minimax_x, minimax_y = _move_to_xy(minimax_result.best_move)
    alphabeta_x, alphabeta_y = _move_to_xy(alphabeta_result.best_move)

    rows.append(
        {
            "State_Name": state_name,
            "Depth_Limit": depth,
            "Minimax_Test_ID": minimax_test_id,
            "AlphaBeta_Test_ID": alphabeta_test_id,
            "Minimax_Algorithm": minimax_row["Algorithm"],
            "AlphaBeta_Algorithm": alphabeta_row["Algorithm"],
            "Minimax_Best_Move_X": minimax_x,
            "Minimax_Best_Move_Y": minimax_y,
            "AlphaBeta_Best_Move_X": alphabeta_x,
            "AlphaBeta_Best_Move_Y": alphabeta_y,
            "Same_Move": minimax_result.best_move == alphabeta_result.best_move,
            "Minimax_Eval_Score": minimax_row["Eval_Score"],
            "AlphaBeta_Eval_Score": alphabeta_row["Eval_Score"],
            "Same_Eval_Score": minimax_row["Eval_Score"] == alphabeta_row["Eval_Score"],
        }
    )


def _move_to_xy(move: tuple[int, int] | None) -> tuple[int | str, int | str]:
    if move is None:
        return "", ""
    row, col = move
    return col, row


if __name__ == "__main__":
    run_benchmark()
