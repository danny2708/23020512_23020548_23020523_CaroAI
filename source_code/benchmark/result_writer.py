import csv
from pathlib import Path


def write_csv(rows: list[dict], output_path: str | Path, fieldnames: list[str]) -> None:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_results_csv(results: list[dict], output_path: str):
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
    write_csv(results, output_path, fieldnames)
