import csv
from pathlib import Path


def write_results_csv(results: list[dict], output_path: str):
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "state",
        "board_size",
        "depth",
        "algorithm",
        "ai_player",
        "best_move",
        "score",
        "nodes_visited",
        "elapsed_time",
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
