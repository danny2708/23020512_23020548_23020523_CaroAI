# Caro AI - Minimax và Alpha-Beta

Project phục vụ bài tập Caro AI.

## Yêu cầu chính

- Bàn cờ Caro kích thước tối thiểu `9x9`.
- Human `X` vs AI `O`.
- Điều kiện thắng: 4 quân liên tiếp theo hàng ngang, dọc hoặc chéo.
- Level 1: Minimax có giới hạn độ sâu.
- Level 2: Alpha-Beta pruning dùng cùng evaluator và cùng depth.
- Level 3: Benchmark Minimax và Alpha-Beta trên cùng trạng thái bàn cờ.

## Cấu trúc

```text
source_code/
|-- main.py
|-- accel/
|   |-- __init__.py
|   `-- caro_accel.pyx
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

## Chạy UI

Từ thư mục gốc:

```bash
cd source_code
python main.py
```

UI có các chế độ:

- Human X vs AI O
- AI X vs AI O
- Benchmark Minimax vs Alpha-Beta

## Các chế độ AI

- `minimax`: Minimax chuẩn trong tập nước đi ứng viên gần quân đã đánh. Chế độ này dùng các tối ưu an toàn như cache đánh giá, transposition table, Zobrist hash và kiểm tra thắng quanh nước cuối.
- `alphabeta`: Alpha-Beta chuẩn trong cùng tập nước đi ứng viên. Move ordering chỉ đổi thứ tự duyệt để cắt tỉa tốt hơn.
- `minimax-improve`: Minimax có thêm beam pruning / forward pruning động.
- `alphabeta-improve`: Alpha-Beta có thêm beam pruning / forward pruning động.

Lưu ý: `*-improve` là chế độ AI thực dụng để chạy depth cao nhanh hơn. Vì beam pruning / forward pruning có thể bỏ qua một số nước hợp lệ, kết quả chọn nước và score có thể khác thuật toán chuẩn.

## AI vs AI

Trong AI X vs AI O:

- `Pause`: dừng autoplay an toàn.
- `Resume`: tiếp tục ván cờ hoặc thêm batch nước mới nếu đã hết giới hạn hiện tại.
- `Swap roles`: lưu trạng thái hiện tại và tạo hai nhánh tiếp diễn.
- `Save state`: lưu bàn cờ và log hiện tại.

Cut-off panel chỉ hiện khi một họ Alpha-Beta bất kỳ đối đầu với một họ Minimax bất kỳ. Nếu là Alpha-Beta vs Alpha-Beta hoặc Minimax vs Minimax thì panel này bị ẩn. Nếu hai AI dùng đúng cùng một mode, UI cũng ẩn `Swap roles` và bàn cờ nhánh phụ vì đổi vai sẽ tạo ra cùng một phiên.

Log và snapshot được lưu dưới:

```text
source_code/results/sessions/
```

## Tối ưu hiệu suất

Pipeline hiện có các tối ưu không làm đổi thuật toán tìm kiếm chuẩn:

- Zobrist hash trên `Board` để tạo key nhanh cho transposition table.
- `cell_codes` dạng số nguyên phẳng trên `Board` để giảm chi phí truy cập grid.
- Transposition table cho Minimax và Alpha-Beta.
- Kiểm tra thắng quanh nước cuối thay vì quét toàn bàn ở mọi node.
- Cache evaluator theo `(board_hash, ai_player)`.
- Optional Cython acceleration cho các hot path:
  - `evaluate_codes`
  - `check_winner_at_codes`
  - `check_winner_full_codes`
  - `quick_move_score_codes`

Nếu chưa build Cython extension, code tự fallback về Python implementation.

## Build Cython acceleration

Cài dependency:

```bash
py -m pip install -r requirements.txt
```

Build extension:

```bash
py setup_accel.py build_ext --inplace
```

Trên Windows cần Microsoft C++ Build Tools. Nếu thiếu compiler, lệnh build sẽ báo lỗi `Microsoft Visual C++ 14.0 or greater is required`; khi đó chương trình vẫn chạy fallback Python.

Kiểm tra extension đã được dùng chưa:

```bash
py -c "import sys; sys.path.insert(0, 'source_code'); from accel import CYTHON_AVAILABLE; print(CYTHON_AVAILABLE)"
```

Kết quả `True` nghĩa là pipeline đang dùng Cython extension.

## Chạy console

```bash
cd source_code
python main.py --console
```

## Chạy benchmark

Từ thư mục gốc:

```bash
python source_code/benchmark/benchmark_runner.py
```

Kết quả benchmark được ghi vào:

```text
source_code/results/benchmark_results.csv
```

## Ghi chú báo cáo

Khi so sánh Minimax và Alpha-Beta, cần dùng:

- cùng trạng thái bàn cờ,
- cùng search depth,
- cùng evaluator,
- cùng move generator.

Nếu dùng `nearby` candidate generation, move ordering, beam width hoặc Cython acceleration, cần mô tả rõ trong báo cáo.
