# Caro AI - Minimax and Alpha-Beta

Project template for the Caro AI assignment.

## Main requirements covered

- 9x9 or larger Caro board.
- Human `X` vs AI `O`.
- Win condition: 4 consecutive stones horizontally, vertically, or diagonally.
- Level 1: Minimax with depth limit.
- Level 2: Alpha-Beta pruning using the same evaluator and depth.
- Level 3: Benchmark Minimax and Alpha-Beta on the same board states.

## Project structure

```text
source_code/
├── main.py
├── core/
│   ├── board.py
│   ├── constants.py
│   ├── move_generator.py
│   └── rules.py
├── ai/
│   ├── base_search.py
│   ├── evaluator.py
│   ├── minimax.py
│   └── alpha_beta.py
├── engine/
│   ├── ai_runner.py
│   └── game_engine.py
├── benchmark/
│   ├── benchmark_runner.py
│   ├── result_writer.py
│   └── test_states.py
├── ui/
│   └── console_ui.py
└── results/
```

## Run desktop UI

From the project root:

```bash
cd source_code
python main.py
```

The UI includes:

- Human X vs AI O
- AI X vs AI O
- Benchmark Minimax vs Alpha-Beta

In AI X vs AI O mode, use `Pause` to stop auto-play safely and `Resume`
to continue. Use `Swap roles`
to save the current board/log and create two continuation branches:

- Branch A keeps the current X/O algorithms.
- Branch B swaps Minimax and Alpha-Beta between X and O.

Set `Next moves after swap` to limit how many additional moves each branch may
play. If a branch reaches that limit, pressing `Resume` adds another batch of
that many moves. The UI logs cut-off nodes per turn, for example
`Turn 14 | Alpha-Beta's nodes: 16352 | Minimax's nodes=17537 | Nodes cut off=1185`,
and keeps a total above the log.
Use `Save state` to save the current board/log without branching. Saved
boards and logs are written under:

```text
source_code/results/sessions/
```

## Run console game

From the project root:

```bash
cd source_code
python main.py --console
```

## Run benchmark

From the project root:

```bash
python source_code/benchmark/benchmark_runner.py
```

The benchmark result will be saved to:

```text
source_code/results/benchmark_results.csv
```

## Notes for report

When comparing Minimax and Alpha-Beta, use:

- the same board state,
- the same search depth,
- the same evaluator,
- the same move generator.

If you use `nearby` candidate move generation or move ordering, describe it clearly in the report.
