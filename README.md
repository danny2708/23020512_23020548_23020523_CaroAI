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
|-- main.py
|-- core/
|   |-- board.py
|   |-- constants.py
|   |-- move_generator.py
|   `-- rules.py
|-- ai/
|   |-- base_search.py
|   |-- evaluator.py
|   |-- minimax.py
|   `-- alpha_beta.py
|-- engine/
|   |-- ai_runner.py
|   |-- auto_play.py
|   `-- game_engine.py
|-- benchmark/
|   |-- benchmark_runner.py
|   |-- result_writer.py
|   `-- test_states.py
|-- ui/
|   |-- console_ui.py
|   `-- tkinter_ui.py
`-- results/
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

## AI modes

UI hiện có 4 chế độ AI:

- `minimax`: Minimax chuẩn trong tập nước đi ứng viên gần quân đã đánh. Chế độ này vẫn dùng các tối ưu an toàn như cache đánh giá, transposition table, Zobrist hash và kiểm tra thắng quanh nước cuối. Các tối ưu này không cố ý bỏ bớt nhánh hợp lệ trong tập ứng viên.
- `alphabeta`: Alpha-Beta chuẩn trong cùng tập nước đi ứng viên. Move ordering chỉ đổi thứ tự duyệt để cắt tỉa tốt hơn, không đổi giá trị minimax lý thuyết trong tập ứng viên đó.
- `minimax-improve`: Minimax có thêm beam pruning / forward pruning động. Chế độ này chỉ duyệt nhóm nước đi được đánh giá hứa hẹn nhất ở mỗi tầng nên nhanh hơn nhiều ở depth cao.
- `alphabeta-improve`: Alpha-Beta có thêm beam pruning / forward pruning động, ngoài move ordering và transposition table.

Lưu ý: `*-improve` là chế độ AI thực dụng để chạy depth 5-8 nhanh hơn. Vì beam pruning / forward pruning có thể bỏ qua một số nước hợp lệ, kết quả chọn nước và score có thể khác với thuật toán chuẩn full-width trong cùng tập ứng viên.

In AI X vs AI O mode, use `Pause` to stop auto-play safely and `Resume`
to continue. Use `Swap roles`
to save the current board/log and create two continuation branches:

- Branch A keeps the current X/O algorithms.
- Branch B swaps Minimax and Alpha-Beta between X and O.

Set `Next moves after swap` to limit how many additional moves each branch may
play. If a branch reaches that limit, pressing `Resume` adds another batch of
that many moves. The UI logs cut-off nodes per turn, for example
`Turn 14 | Alpha-Beta's nodes: 16352 | Minimax's nodes=17537 | Nodes cut off=1185`,
and keeps a total above the log. This cut-off panel is shown only when any
Alpha-Beta mode is compared against any Minimax mode; it is hidden for
Alpha-Beta vs Alpha-Beta or Minimax vs Minimax.
If both AI players use exactly the same mode, the UI hides `Swap roles` and
the secondary branch board because swapping would produce the same session.
Use `Save state` to save the current board/log without branching. Saved
boards and logs are written under:

```text
source_code/results/sessions/
```

## Search performance

The search pipeline uses several optimizations so higher depths stay usable:

- Zobrist hash on `Board` for fast transposition table keys.
- Transposition tables in both Minimax and Alpha-Beta.
- Winner checks around the last move instead of scanning the whole board at every node.
- Cached evaluator windows and evaluation results.
- Tactical move ordering that prioritizes immediate wins, forced blocks, and strong local patterns.
- Dynamic beam width in `*-improve` modes: depth 5-6 uses a moderate candidate limit, depth 7-8 uses a stricter deep-search beam, and depth 9+ uses an ultra-deep tactical beam.

Because of the beam width, high-depth `*-improve` search is practical forward-pruned search, not a full-width exhaustive tree.
This keeps depth 5-8 responsive and prevents deeper runs from exploding combinatorially.

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

If you use `nearby` candidate move generation, move ordering, or beam width, describe it clearly in the report.
