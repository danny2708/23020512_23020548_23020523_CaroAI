# Caro AI - Minimax và Alpha-Beta

Project phục vụ bài tập AI cờ Caro. Chương trình hỗ trợ chơi `Human vs AI`, `AI vs AI` và chạy benchmark để so sánh Minimax với Alpha-Beta.

## 1. Yêu cầu môi trường

- Python `>= 3.10`.
- Hệ điều hành Windows/Linux/macOS đều có thể chạy bản Python thuần.
- Giao diện dùng `tkinter`; nếu cài thêm `ttkbootstrap` thì UI sẽ dùng theme hiện đại hơn.

Cài thư viện:

```powershell
py -m pip install -r requirements.txt
```

Nếu chỉ muốn chạy logic Python cơ bản, chương trình vẫn có thể fallback khi chưa build Cython.

## 2. Cấu trúc thư mục chính

```text
source_code/
|-- main.py                    # Điểm chạy chương trình
|-- core/                      # Board, luật chơi, sinh nước đi
|-- ai/                        # Minimax, Alpha-Beta, evaluator
|-- engine/                    # Điều phối ván chơi
|-- ui/                        # Tkinter UI và console UI
|-- benchmark/                 # Bộ benchmark và xuất CSV
`-- results/                   # Kết quả benchmark, log, session
```

Tài liệu báo cáo nằm trong:

```text
docs/bao_cao_caro_ai.md
```

## 3. Chạy giao diện chính

Từ thư mục gốc project:

```powershell
py source_code\main.py
```

Giao diện có ba tab:

- `Human vs AI`: người chơi `X` đánh với AI `O`.
- `AI vs AI`: hai AI tự đánh với nhau, có thể pause/resume/back step/swap roles.
- `Benchmark`: chạy thực nghiệm so sánh thuật toán và xuất file CSV.

## 4. Chạy console

Nếu muốn chạy bản console:

```powershell
py source_code\main.py --console
```

Bản console phù hợp để kiểm tra nhanh logic trò chơi, nhưng để dùng đầy đủ các chức năng hiện tại nên chạy UI.

## 5. Các chế độ AI

Trong UI, các lựa chọn AI gồm:

- `1 - minimax`: Minimax chuẩn.
- `2 - alphabeta`: Alpha-Beta chuẩn, dùng cùng evaluator và cùng độ sâu với Minimax khi so sánh.
- `3 - minimax-improve`: Minimax có thêm giới hạn ứng viên/beam pruning/forward pruning để chạy depth cao nhanh hơn.
- `4 - alphabeta-improve`: Alpha-Beta có thêm các cải tiến tương tự.

Lưu ý cho báo cáo: hai mode `*-improve` là chế độ thực dụng để tăng tốc. Vì có thể bỏ qua một số nước hợp lệ, chúng không nên dùng để chứng minh Alpha-Beta tương đương Minimax chuẩn. Khi so sánh lý thuyết, dùng `minimax` và `alphabeta`.

## 6. Cách dùng nhanh trong UI

### Human vs AI

1. Chọn `Board size`, `AI mode`, `Depth`.
2. Nhấn `New game`.
3. Click ô trống để đánh quân `X`.
4. AI tự đánh quân `O`.
5. Có thể dùng `Back step` để lùi lại lượt gần nhất, sau đó đổi model/depth cho nước tiếp theo.

### AI vs AI

1. Chọn thuật toán cho `X AI` và `O AI`.
2. Chọn `Depth`, `Max turns`, `Next moves`.
3. Nhấn `New game`, `Step` hoặc `Run all`.
4. `Pause` dừng ván hiện tại.
5. `Resume` chạy tiếp theo số nước đặt trong `Next moves`.
6. `Back step` lùi một nước sau khi pause.
7. `Swap roles` tạo nhánh phụ khi hai AI khác vai trò/thuật toán.
8. `Save state` lưu thế cờ và log vào `source_code/results/sessions/`.

## 7. Chạy benchmark

Từ thư mục gốc project:

```powershell
py source_code\benchmark\benchmark_runner.py
```

Benchmark mặc định chạy 5 thế cờ kiểm thử với các depth `1`, `2`, `3`, `4`, so sánh `Minimax` và `Alpha-Beta` trên cùng trạng thái, cùng evaluator và cùng move generator.

Các file kết quả được ghi vào:

```text
source_code/results/benchmark_summary.csv
source_code/results/pruning_details.csv
source_code/results/eval_heuristic_log.csv
source_code/results/move_matching.csv
```

Ý nghĩa các file:

- `benchmark_summary.csv`: kết quả tổng quan theo từng test, gồm thuật toán, depth, best move, score, số node, thời gian chạy và trạng thái thắng/thua được phát hiện.
- `pruning_details.csv`: chi tiết các lần Alpha-Beta cắt nhánh, gồm depth cắt, alpha, beta, số node ước lượng đã bỏ qua và timestamp.
- `eval_heuristic_log.csv`: breakdown heuristic cho các nước ứng viên ở root, gồm điểm tấn công, phòng thủ, vị trí và tổng điểm.
- `move_matching.csv`: bảng đối chiếu trực tiếp câu hỏi “Alpha-Beta có chọn cùng nước đi với Minimax không?”. Cột `Same_Move=True` nghĩa là hai thuật toán chọn cùng nước đi ở cùng `State_Name` và `Depth_Limit`.

Tọa độ trong CSV dùng dạng `(X, Y)`, trong đó `X` là cột, `Y` là hàng và đều bắt đầu từ `0`.

## 8. Build Cython acceleration tùy chọn

Để tăng tốc một số hot path:

```powershell
py setup_accel.py build_ext --inplace
```

Kiểm tra extension đã được dùng chưa:

```powershell
py -c "import sys; sys.path.insert(0, 'source_code'); from accel import CYTHON_AVAILABLE; print(CYTHON_AVAILABLE)"
```

Nếu kết quả là `True`, chương trình đang dùng Cython. Nếu build lỗi do thiếu compiler, chương trình vẫn chạy bằng Python thuần.
