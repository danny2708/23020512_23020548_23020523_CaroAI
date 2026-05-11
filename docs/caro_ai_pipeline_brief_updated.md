# Kim chỉ nam xây dựng pipeline Caro AI

Tài liệu này dùng làm bối cảnh kỹ thuật cho agent khi xây dựng project Caro AI. Agent cần đọc tài liệu này cùng với file đề bài `De_so_1.pdf` trước khi triển khai. Mục tiêu là xây dựng pipeline đúng yêu cầu bài tập, có thể chạy Human vs AI, có thể chạy benchmark Minimax vs Alpha-Beta, và có đủ dữ liệu để viết báo cáo thực nghiệm.

Phiên bản này đã được bổ sung thêm các ý có thể áp dụng từ notebook `benchmark_analysis.ipynb` của repo tham khảo `MonHauVD/Caro_AI`, nhưng chỉ lấy các phần phù hợp với đề bài: đọc CSV benchmark, phân tích bằng pandas, so sánh cùng board/cùng depth/cùng evaluator, tính phần trăm giảm node/thời gian, kiểm tra hai thuật toán có chọn cùng nước đi không, và có thể lưu final board để phục vụ báo cáo.

---

## 1. Bối cảnh bài toán

Project cần xây dựng một chương trình chơi cờ Caro giữa người chơi và máy tính. Chương trình có thể chạy bằng console, không bắt buộc có giao diện đồ họa.

Các yêu cầu chính:

- Bàn cờ có kích thước tối thiểu `9x9`.
- Người chơi có thể dùng quân `X`.
- Máy có thể dùng quân `O`.
- Ô trống được biểu diễn bằng dấu chấm `.`.
- Hai bên đánh luân phiên.
- Không được đánh vào ô đã có quân.
- Người thắng là người có `4` quân liên tiếp theo hàng ngang, hàng dọc, đường chéo chính hoặc đường chéo phụ.
- Không xét luật chặn hai đầu.
- Nếu bàn cờ đầy và không có người thắng thì kết quả là hòa.

Project cần hoàn thành ba mức chính:

- Level 1: AI chơi Caro bằng Minimax có giới hạn độ sâu.
- Level 2: Cải tiến bằng Alpha-Beta pruning.
- Level 3: Benchmark và phân tích hiệu quả Minimax so với Alpha-Beta trên nhiều trạng thái bàn cờ.

---

## 2. Nguyên tắc thiết kế bắt buộc

Pipeline phải dùng chung cho Minimax và Alpha-Beta. Khi chuyển thuật toán, chỉ thay module tìm kiếm, không thay luật chơi, board, evaluator, move generator hoặc benchmark.

Các nguyên tắc cần giữ:

- Ưu tiên đúng đề hơn độ mạnh của AI.
- Luật thắng luôn là `4` quân liên tiếp.
- Không dùng luật Gomoku `5` quân.
- Không hard-code `O` luôn là AI trong evaluator và search.
- Mỗi searcher phải biết nó đang tìm nước đi cho player nào thông qua `ai_player`.
- Trong cây Minimax/Alpha-Beta:
  - lượt của `ai_player` là MAX, chọn giá trị lớn nhất;
  - lượt của đối thủ là MIN, chọn giá trị nhỏ nhất.
- Evaluator phải đánh giá theo góc nhìn của `ai_player`:
  - điểm dương là tốt cho `ai_player`;
  - điểm âm là tốt cho đối thủ.
- Minimax và Alpha-Beta phải dùng cùng evaluator khi so sánh.
- Minimax và Alpha-Beta phải dùng cùng độ sâu khi benchmark.
- Minimax và Alpha-Beta phải chạy trên cùng trạng thái bàn cờ khi benchmark.
- Candidate moves và move ordering chỉ là tối ưu hợp lệ, không được làm sai khái niệm nước đi hợp lệ.
- Nếu có lọc candidate moves hoặc move ordering, phải dùng giống nhau cho cả Minimax và Alpha-Beta trong benchmark.
- Không dùng machine learning model, neural network hoặc thư viện có sẵn để thay phần thuật toán chính.

---

## 3. Luồng hoạt động tổng quát

### 3.1. Luồng Human vs AI

1. Khởi tạo bàn cờ.
2. Người chơi chọn chế độ AI: Minimax hoặc Alpha-Beta.
3. Người chơi chọn độ sâu tìm kiếm.
4. Chương trình hiển thị bàn cờ.
5. Người chơi nhập nước đi.
6. Chương trình kiểm tra nước đi hợp lệ.
7. Chương trình đặt quân của người chơi.
8. Chương trình kiểm tra thắng hoặc hòa.
9. Nếu game chưa kết thúc, AI tìm nước đi tốt nhất.
10. AI đặt quân lên bàn cờ.
11. Chương trình log nước đi AI, score, depth, nodes visited và elapsed time.
12. Chương trình kiểm tra thắng hoặc hòa.
13. Lặp lại cho đến khi có người thắng hoặc hòa.

### 3.2. Luồng AI vs AI

AI vs AI là mode mở rộng để demo chương trình có thể tự chơi. Không dùng AI vs AI làm benchmark chính để kết luận Alpha-Beta tốt hơn Minimax, vì mỗi thuật toán ở các lượt khác nhau sẽ chạy trên các trạng thái khác nhau.

Luồng AI vs AI:

1. Khởi tạo bàn cờ.
2. Chọn thuật toán cho player `X`.
3. Chọn thuật toán cho player `O`.
4. Chọn cùng một độ sâu hoặc cho phép nhập depth riêng nếu muốn demo.
5. Với mỗi lượt:
   - xác định `current_player`;
   - tạo searcher cho player đó;
   - gọi `search(board, ai_player=current_player, depth=...)`;
   - đặt quân;
   - in board và log kết quả.
6. Dừng khi có người thắng, hòa, hoặc đạt `max_turns` do người dùng nhập.

Yêu cầu quan trọng cho AI vs AI:

- Không được mặc định `O` là AI.
- Khi `X` tìm nước đi, `X` là MAX và `O` là MIN.
- Khi `O` tìm nước đi, `O` là MAX và `X` là MIN.
- Nếu log cho thấy một player không chặn nước thắng rõ ràng của đối thủ, cần kiểm tra lại evaluator và vai trò `ai_player`.

### 3.3. Luồng benchmark

Benchmark là luồng chính để làm Level 3 và báo cáo.

1. Tải danh sách trạng thái kiểm thử.
2. Với mỗi trạng thái, tạo lại board tương ứng.
3. Với mỗi depth, ví dụ `1`, `2`, `3`:
   - chạy Minimax trên board gốc;
   - chạy Alpha-Beta trên board gốc clone lại;
   - dùng cùng `ai_player`, cùng evaluator, cùng move generator;
   - ghi best move, score, số node đã xét và thời gian chạy.
4. Tạo thêm dòng so sánh giữa Minimax và Alpha-Beta:
   - có chọn cùng nước đi không;
   - có cùng score không;
   - Alpha-Beta giảm bao nhiêu node;
   - Alpha-Beta giảm bao nhiêu thời gian.
5. Ghi toàn bộ kết quả ra CSV.
6. Có thể ghi thêm final board hoặc board input dạng ASCII để tiện đưa vào báo cáo.
7. Dùng CSV để viết phần phân tích trong báo cáo hoặc đọc bằng notebook.

---

## 4. Cấu trúc dự án đề xuất

```text
source_code/
├── main.py
├── config.py
├── core/
│   ├── __init__.py
│   ├── constants.py
│   ├── board.py
│   ├── rules.py
│   └── move_generator.py
├── ai/
│   ├── __init__.py
│   ├── base_search.py
│   ├── evaluator.py
│   ├── minimax.py
│   └── alpha_beta.py
├── engine/
│   ├── __init__.py
│   ├── ai_runner.py
│   └── game_engine.py
├── ui/
│   ├── __init__.py
│   └── console_ui.py
├── benchmark/
│   ├── __init__.py
│   ├── test_states.py
│   ├── benchmark_runner.py
│   ├── result_writer.py
│   └── board_writer.py
└── results/
    ├── benchmark_results.csv
    ├── benchmark_comparison.csv
    └── boards/

notebooks/
└── benchmark_analysis.ipynb

docs/
└── pipeline_modules.md

README.md
requirements.txt
.gitignore
```

Ghi chú:

- `source_code/results/benchmark_results.csv`: lưu kết quả raw, mỗi dòng là một lần chạy một thuật toán.
- `source_code/results/benchmark_comparison.csv`: lưu kết quả ghép cặp Minimax vs Alpha-Beta trên cùng state/depth/player.
- `source_code/results/boards/`: lưu input board hoặc final board nếu cần minh họa.
- `notebooks/benchmark_analysis.ipynb`: notebook phân tích kết quả benchmark, làm đơn giản hơn repo tham khảo.

---

## 5. Module `core`

Nhóm `core` chứa các thành phần nền tảng của trò chơi. Những module này không phụ thuộc vào Minimax hay Alpha-Beta.

### 5.1. `core/constants.py`

Mục đích:

- Tập trung các hằng số của game.
- Tránh lặp magic number hoặc hard-code ký hiệu quân cờ ở nhiều nơi.

Cần có:

```python
EMPTY = "."
PLAYER_X = "X"
PLAYER_O = "O"
DEFAULT_BOARD_SIZE = 9
MIN_BOARD_SIZE = 9
WIN_LENGTH = 4
DIRECTIONS = [(0, 1), (1, 0), (1, 1), (1, -1)]
```

Có thể có thêm trạng thái:

```python
STATUS_PLAYING = "PLAYING"
STATUS_DRAW = "DRAW"
STATUS_X_WIN = "X_WIN"
STATUS_O_WIN = "O_WIN"
```

### 5.2. `core/board.py`

Mục đích:

- Quản lý trạng thái bàn cờ.
- Cung cấp thao tác đặt quân, hoàn tác và truy vấn board.

Cần xây dựng class `Board`.

Các hàm cần có:

- `__init__(size=DEFAULT_BOARD_SIZE, grid=None)`: tạo board với kích thước tối thiểu 9x9.
- `is_inside(row, col)`: kiểm tra tọa độ có nằm trong bàn cờ không.
- `is_empty_cell(row, col)`: kiểm tra một ô có trống không.
- `place_move(row, col, player)`: đặt quân nếu nước đi hợp lệ.
- `undo_move(row, col)`: hoàn tác nước đi.
- `get_empty_cells()`: lấy danh sách ô trống.
- `get_occupied_cells()`: lấy danh sách ô đã có quân.
- `is_full()`: kiểm tra board đã đầy chưa.
- `clone()`: tạo bản sao board nếu cần.
- `to_strings()`: chuyển board thành list string.
- `to_ascii()`: chuyển board thành text có chỉ số hàng/cột để lưu log.
- `display()`: in bàn cờ ra console nếu cần.

Yêu cầu quan trọng:

- Không cho đặt quân ngoài bàn cờ.
- Không cho đặt quân vào ô đã có quân.
- Search nên dùng `place_move` rồi `undo_move` để tránh clone quá nhiều.
- `clone` vẫn cần cho benchmark để đảm bảo Minimax và Alpha-Beta chạy trên board độc lập.

### 5.3. `core/rules.py`

Mục đích:

- Xử lý luật thắng, hòa và trạng thái kết thúc.

Các hàm cần có:

- `check_winner(board, player)`: kiểm tra một player đã thắng chưa.
- `check_draw(board)`: kiểm tra bàn cờ hòa chưa.
- `get_game_status(board)`: trả về trạng thái hiện tại của ván đấu.
- `is_terminal(board)`: trả về `True` nếu X thắng, O thắng hoặc hòa.

Trạng thái game nên có:

- `PLAYING`
- `X_WIN`
- `O_WIN`
- `DRAW`

Yêu cầu quan trọng:

- Chỉ cần 4 quân liên tiếp là thắng.
- Kiểm tra đủ 4 hướng.
- Không xét luật chặn hai đầu.
- Không được dùng luật 5 quân của Gomoku.

### 5.4. `core/move_generator.py`

Mục đích:

- Sinh danh sách nước đi hợp lệ cho thuật toán tìm kiếm.
- Có thể giảm không gian tìm kiếm bằng candidate moves.

Các hàm cần có:

- `generate_legal_moves(board)`: trả về toàn bộ ô trống.
- `generate_candidate_moves(board, radius=1)`: trả về các ô trống gần những quân đã đánh.
- `order_moves(board, moves, ai_player)`: sắp xếp nước đi nếu cần.

Yêu cầu quan trọng:

- Nếu board trống, candidate move nên là ô trung tâm.
- Nếu board đã có quân, candidate moves chỉ chọn các ô trống gần quân đã đánh.
- Nếu candidate moves rỗng vì lỗi logic, fallback về toàn bộ legal moves.
- Nếu có lọc hoặc sắp xếp candidate moves, phải dùng giống nhau cho Minimax và Alpha-Beta trong benchmark.
- Nếu có move ordering, cần ghi rõ trong README hoặc báo cáo.

Khuyến nghị triển khai ban đầu:

- Dùng `generate_candidate_moves(radius=1)` hoặc `radius=2`.
- Với board 9x9, `radius=1` đã đủ để giảm node đáng kể.
- Move ordering có thể đơn giản: ưu tiên ô gần trung tâm, sau đó ưu tiên ô có điểm evaluator cao khi giả lập đặt quân.

---

## 6. Module `ai`

Nhóm `ai` chứa evaluator và các thuật toán tìm kiếm. Tất cả thuật toán phải dùng chung board, rules và move generator.

### 6.1. `ai/evaluator.py`

Mục đích:

- Đánh giá trạng thái bàn cờ khi chưa đạt terminal state hoặc khi đã hết độ sâu tìm kiếm.
- Trả điểm theo góc nhìn của `ai_player`.

Cần xây dựng class `Evaluator`.

Các hàm cần có:

- `evaluate(board, ai_player) -> int`: nhận board và `ai_player`, trả về điểm đánh giá.
- `get_opponent(player) -> str`: xác định đối thủ.
- `score_line(line, ai_player) -> int`: đánh giá một đoạn/hàng/đường chéo.
- Hàm phụ để duyệt tất cả hàng, cột, chéo chính, chéo phụ.

Tiêu chí đánh giá gợi ý:

| Tình huống | Điểm gợi ý |
|---|---:|
| `ai_player` có 4 quân liên tiếp | `+100000` |
| đối thủ có 4 quân liên tiếp | `-100000` |
| `ai_player` có 3 quân liên tiếp còn có khả năng mở rộng | `+1000` đến `+3000` |
| đối thủ có 3 quân liên tiếp còn có khả năng mở rộng | `-2000` đến `-5000` |
| `ai_player` có 2 quân liên tiếp | `+100` |
| đối thủ có 2 quân liên tiếp | `-200` |
| `ai_player` có 1 quân | `+10` |
| đối thủ có 1 quân | `-10` |

Yêu cầu quan trọng:

- Không gọi evaluator là machine learning model.
- Không hard-code `O` là AI.
- Điểm tốt cho `ai_player` phải là điểm dương.
- Điểm tốt cho đối thủ phải là điểm âm.
- Đối thủ có 3 quân liên tiếp nên bị phạt mạnh hơn để AI ưu tiên chặn.
- Terminal score nên được xử lý thống nhất với `rules.py` để tránh evaluator và search mâu thuẫn.

Ví dụ tư duy đúng:

```text
Nếu ai_player = X:
- X tạo chuỗi tốt => cộng điểm.
- O tạo chuỗi tốt => trừ điểm.

Nếu ai_player = O:
- O tạo chuỗi tốt => cộng điểm.
- X tạo chuỗi tốt => trừ điểm.
```

### 6.2. `ai/base_search.py`

Mục đích:

- Định nghĩa kết quả search dùng chung.
- Định nghĩa interface chung cho Minimax và Alpha-Beta.
- Chứa helper dùng chung nếu cần.

Cần có dataclass `SearchResult`:

```python
@dataclass
class SearchResult:
    best_move: tuple[int, int] | None
    score: int
    depth: int
    nodes_visited: int
    elapsed_time: float
    algorithm: str
    player: str
```

Có thể bổ sung các trường sau để log tốt hơn:

```python
candidate_count: int | None = None
status: str | None = None
```

Các hàm cần có:

- `search(board, ai_player, depth)`: interface chung cho các thuật toán.
- `get_opponent(player)`: lấy đối thủ của một player.
- `terminal_score(board, ai_player, current_depth=None)`: tính điểm kết thúc theo góc nhìn của `ai_player`.

Gợi ý terminal score:

```text
ai_player thắng: +100000
ai_player thua:  -100000
hòa: 0
```

Có thể cộng/trừ nhẹ theo depth để ưu tiên thắng sớm và thua muộn:

```text
ai_player thắng: +100000 + depth_remaining
ai_player thua:  -100000 - depth_remaining
```

Không bắt buộc, nhưng nếu dùng thì phải dùng giống nhau cho cả Minimax và Alpha-Beta.

### 6.3. `ai/minimax.py`

Mục đích:

- Cài đặt thuật toán Minimax cho Level 1.

Cần xây dựng class `MinimaxSearch`.

Các hàm cần có:

- `search(board, ai_player, depth)`: hàm public để AI tìm nước đi.
- `_minimax(board, depth, current_player, ai_player)`: hàm đệ quy xử lý MAX/MIN.

Yêu cầu thuật toán:

- Nếu trạng thái là thắng, thua hoặc hòa, trả về điểm kết thúc.
- Nếu đạt giới hạn độ sâu, gọi evaluator.
- Nếu `current_player == ai_player`, chọn giá trị lớn nhất.
- Nếu `current_player != ai_player`, chọn giá trị nhỏ nhất.
- Trả về nước đi tốt nhất và score tương ứng.
- Đếm số trạng thái đã xét.
- Đo thời gian chạy.

Pseudocode định hướng:

```text
search(board, ai_player, depth):
    start timer
    nodes = 0
    best_score = -inf
    best_move = None
    for move in candidate_moves:
        place move for ai_player
        score = _minimax(board, depth - 1, opponent(ai_player), ai_player)
        undo move
        choose max score
    return SearchResult(...)
```

Trong `_minimax`:

```text
if terminal: return terminal_score
if depth == 0: return evaluator.evaluate(board, ai_player)
if current_player == ai_player: maximize
else: minimize
```

### 6.4. `ai/alpha_beta.py`

Mục đích:

- Cài đặt Alpha-Beta pruning cho Level 2.

Cần xây dựng class `AlphaBetaSearch`.

Các hàm cần có:

- `search(board, ai_player, depth)`: hàm public để AI tìm nước đi.
- `_alpha_beta(board, depth, alpha, beta, current_player, ai_player)`: hàm đệ quy có alpha và beta.

Yêu cầu thuật toán:

- Dùng cùng evaluator với Minimax.
- Dùng cùng move generator với Minimax khi benchmark.
- Dùng cùng depth với Minimax khi so sánh.
- Nếu là nhánh MAX, cập nhật `alpha`.
- Nếu là nhánh MIN, cập nhật `beta`.
- Cắt nhánh khi `beta <= alpha`.
- Trả về cùng kiểu `SearchResult` như Minimax.

Pseudocode định hướng:

```text
if terminal: return terminal_score
if depth == 0: return evaluator.evaluate(board, ai_player)

if current_player == ai_player:
    value = -inf
    for move in moves:
        place current_player
        value = max(value, recursive_result)
        undo
        alpha = max(alpha, value)
        if beta <= alpha: break
    return value
else:
    value = +inf
    for move in moves:
        place current_player
        value = min(value, recursive_result)
        undo
        beta = min(beta, value)
        if beta <= alpha: break
    return value
```

---

## 7. Module `engine`

Nhóm `engine` điều phối giữa UI, board, rules và AI.

### 7.1. `engine/ai_runner.py`

Mục đích:

- Tạo đúng searcher theo chế độ người dùng chọn.
- Giúp game engine không phụ thuộc trực tiếp vào class cụ thể.

Các hàm cần có:

- `create_searcher(algorithm, evaluator=None, move_generator=None)`: nhận tên thuật toán và trả về Minimax hoặc Alpha-Beta searcher.
- `normalize_algorithm_name(name)`: chuẩn hóa tên thuật toán nếu cần.

Các mode cần hỗ trợ:

- `minimax`
- `alphabeta`
- `alpha-beta`
- `alpha_beta`

### 7.2. `engine/game_engine.py`

Mục đích:

- Điều phối ván chơi Human vs AI.
- Điều phối mode AI vs AI nếu triển khai.
- Quản lý lượt chơi.
- Gọi searcher để AI chọn nước.
- Kiểm tra trạng thái kết thúc sau mỗi lượt.

Các hàm cần có:

- `run_human_vs_ai()`
- `run_ai_vs_ai()` nếu có
- `handle_human_turn()`
- `handle_ai_turn(ai_player, algorithm, depth)`
- `check_and_print_game_status()`
- `log_ai_result(result)`

Yêu cầu quan trọng:

- Human vs AI là mode chính.
- Người chơi mặc định là `X`.
- AI mặc định là `O`.
- AI có thể dùng Minimax hoặc Alpha-Beta.
- Sau lượt AI phải hiển thị nước đi, score, depth, nodes visited và elapsed time.
- AI vs AI chỉ là mode demo, không dùng làm bảng so sánh chính trong báo cáo.

---

## 8. Module `ui`

### 8.1. `ui/console_ui.py`

Mục đích:

- Cung cấp giao diện console đơn giản.
- Đọc input an toàn.
- In board và thông báo trạng thái game.

Các hàm cần có:

- `show_main_menu()`: hiển thị menu chính.
- `read_board_size()`: đọc kích thước board.
- `read_ai_mode()`: đọc thuật toán AI.
- `read_depth()`: đọc độ sâu tìm kiếm.
- `read_max_turns()`: đọc số lượt tối đa cho AI vs AI nếu cần.
- `read_player_move()`: đọc nước đi người chơi.
- `print_board(board)`: in bàn cờ.
- `print_ai_result(result)`: in kết quả tìm kiếm của AI.
- `print_game_status(status)`: in kết quả thắng, thua hoặc hòa.

Yêu cầu xử lý input:

- Người dùng nhập không phải số.
- Người dùng nhập tọa độ ngoài board.
- Người dùng nhập vào ô đã có quân.
- Người dùng nhập board size nhỏ hơn 9.
- Người dùng nhập thuật toán không hợp lệ.

---

## 9. Module `benchmark`

Nhóm `benchmark` phục vụ Level 3 và báo cáo thực nghiệm.

### 9.1. `benchmark/test_states.py`

Mục đích:

- Chuẩn bị các trạng thái bàn cờ để kiểm thử Minimax và Alpha-Beta.
- Đảm bảo hai thuật toán chạy trên cùng dữ liệu.

Cần có ít nhất 5 trạng thái, nên có 6 trạng thái để báo cáo phong phú hơn:

1. `empty_board`: trạng thái đầu ván.
2. `early_game`: trạng thái đầu hoặc gần đầu ván.
3. `mid_game`: trạng thái giữa ván.
4. `ai_can_win`: AI có thể thắng ngay.
5. `ai_must_block`: người chơi sắp thắng, AI cần chặn.
6. `both_attack`: hai bên đều có cơ hội tấn công hoặc có nhiều nước đi hợp lệ.

Các hàm cần có:

- `board_from_strings(rows)`: tạo board từ danh sách chuỗi.
- `get_test_states()`: trả về danh sách test case.
- `validate_state(rows)`: validate trạng thái nếu cần.

Mỗi test case nên có cấu trúc:

```python
{
    "name": "ai_must_block",
    "description": "X có 3 quân liên tiếp, O cần chặn",
    "rows": [
        ".........",
        ".........",
        "...XXX...",
        "....O....",
        ".........",
        ".........",
        ".........",
        ".........",
        ".........",
    ],
    "ai_player": "O",
    "expected_type": "block"
}
```

### 9.2. `benchmark/benchmark_runner.py`

Mục đích:

- Chạy thực nghiệm so sánh Minimax và Alpha-Beta.
- Thu thập dữ liệu cho báo cáo.

Các hàm cần có:

- `run_benchmark(depths=(1, 2, 3))`: chạy toàn bộ benchmark.
- `run_single_case(state, algorithm, depth)`: chạy một thuật toán trên một trạng thái cụ thể.
- `compare_pair(minimax_result, alphabeta_result)`: tạo dòng so sánh giữa hai thuật toán.
- Hàm tạo evaluator và searcher dùng chung.
- Hàm tổng hợp kết quả.

Mỗi dòng raw result cần có:

- `case_id`
- `case_name`
- `description`
- `board_size`
- `depth`
- `algorithm`
- `ai_player`
- `best_move_row`
- `best_move_col`
- `best_move`
- `score`
- `nodes_visited`
- `elapsed_time_sec`
- `candidate_count` nếu có
- `input_board_ascii` hoặc đường dẫn tới file board

Yêu cầu quan trọng:

- Minimax và Alpha-Beta phải chạy trên cùng state.
- Mỗi thuật toán phải nhận board clone riêng để không làm bẩn trạng thái.
- Minimax và Alpha-Beta phải dùng cùng depth.
- Minimax và Alpha-Beta phải dùng cùng evaluator.
- Minimax và Alpha-Beta phải dùng cùng move generator.
- `ai_player` trong benchmark nên mặc định là `O` để khớp bài Human vs AI, nhưng code vẫn phải hỗ trợ `X`.

### 9.3. `benchmark/result_writer.py`

Mục đích:

- Ghi kết quả benchmark ra file CSV.
- Tạo thư mục output nếu chưa có.

Các hàm cần có:

- `write_results(rows, output_path)`: ghi danh sách kết quả raw ra CSV.
- `write_comparison(rows, output_path)`: ghi bảng so sánh Minimax vs Alpha-Beta ra CSV.
- Hàm tạo thư mục `results` nếu cần.
- Hàm in summary ngắn nếu cần.

Output mặc định:

- `source_code/results/benchmark_results.csv`
- `source_code/results/benchmark_comparison.csv`

### 9.4. `benchmark/board_writer.py`

Mục đích:

- Lưu input board hoặc final board thành file text để dễ kiểm tra và đưa vào báo cáo.
- Học ý tưởng từ notebook tham khảo: có thể tra cứu board theo `case_id` hoặc `match_id`.

Các hàm cần có:

- `write_board_ascii(board, path)`: ghi một board thành file text.
- `write_case_boards(test_states, output_dir)`: ghi toàn bộ board kiểm thử.
- `board_to_ascii(board)`: chuyển board sang text có chỉ số hàng/cột.

Output gợi ý:

```text
source_code/results/boards/empty_board.txt
source_code/results/boards/ai_must_block.txt
source_code/results/boards/both_attack.txt
```

### 9.5. Bảng so sánh pairwise

Ngoài raw CSV, cần tạo bảng so sánh ghép cặp Minimax và Alpha-Beta. Mỗi dòng là một cặp chạy trên cùng `case_name`, cùng `depth`, cùng `ai_player`.

Các cột nên có:

- `case_name`
- `depth`
- `ai_player`
- `minimax_best_move`
- `alphabeta_best_move`
- `same_best_move`
- `minimax_score`
- `alphabeta_score`
- `same_score`
- `minimax_nodes`
- `alphabeta_nodes`
- `node_reduction`
- `node_reduction_percent`
- `minimax_time_sec`
- `alphabeta_time_sec`
- `time_reduction_sec`
- `time_reduction_percent`

Công thức:

```text
node_reduction = minimax_nodes - alphabeta_nodes
node_reduction_percent = node_reduction / minimax_nodes * 100

time_reduction_sec = minimax_time_sec - alphabeta_time_sec
time_reduction_percent = time_reduction_sec / minimax_time_sec * 100
same_best_move = minimax_best_move == alphabeta_best_move
same_score = minimax_score == alphabeta_score
```

Lưu ý:

- `same_best_move` không phải lúc nào cũng `True`, đặc biệt nếu có nhiều nước đi có cùng score.
- `same_score` nên giống nhau nếu cùng depth, cùng evaluator, cùng candidate list và không có bug.
- Alpha-Beta thường có `nodes_visited <= Minimax`, nhưng nếu cách đếm node khác nhau thì cần chuẩn hóa trước khi kết luận.

---

## 10. `main.py`

Mục đích:

- Là entry point của chương trình.
- Kết nối UI, game engine và benchmark runner.

Menu nên có:

```text
=== CARO AI ===
1. Human X vs AI O
2. AI X vs AI O
3. Benchmark Minimax vs Alpha-Beta
4. Exit
```

Luồng chính:

1. Hiển thị menu.
2. Người dùng chọn Human vs AI, AI vs AI hoặc benchmark.
3. Nếu chọn Human vs AI, đọc board size, thuật toán và depth rồi chạy game.
4. Nếu chọn AI vs AI, đọc board size, thuật toán của X, thuật toán của O, depth và max turns.
5. Nếu chọn benchmark, chạy benchmark runner và ghi CSV.
6. In thông báo kết quả.

Yêu cầu quan trọng:

- Human vs AI là mode chính để demo đúng yêu cầu đề.
- Benchmark là mode chính để lấy số liệu báo cáo.
- AI vs AI là mode mở rộng để kiểm tra pipeline tự chơi.
- Không dùng AI vs AI log để kết luận trực tiếp Alpha-Beta giảm node tốt hơn Minimax, vì hai thuật toán có thể chạy trên các trạng thái khác nhau.

---

## 11. `README.md`

README cần phục vụ nộp bài và chạy chương trình.

Nội dung cần có:

- Tên project.
- Mô tả ngắn bài toán.
- Yêu cầu môi trường.
- Cách cài dependencies.
- Cách chạy Human vs AI.
- Cách chạy AI vs AI nếu có.
- Cách chạy benchmark.
- Vị trí file kết quả benchmark.
- Vị trí notebook phân tích nếu có.
- Mô tả ngắn Minimax.
- Mô tả ngắn Alpha-Beta.
- Mô tả ngắn evaluator.
- Ghi chú nếu có dùng candidate moves hoặc move ordering.
- Phần đã tham khảo từ hai repo mẫu.
- Cam kết không copy nguyên code thuật toán chính.

Lệnh chạy gợi ý:

```bash
cd source_code
py main.py
```

Chạy benchmark trực tiếp:

```bash
py source_code/benchmark/benchmark_runner.py
```

Mở notebook phân tích:

```bash
jupyter notebook notebooks/benchmark_analysis.ipynb
```

---

## 12. Logging

Mỗi lần AI chọn nước đi, chương trình cần ghi hoặc in:

- Thuật toán đang dùng.
- Player của AI.
- Nước đi được chọn.
- Score.
- Depth.
- Số trạng thái đã xét.
- Thời gian chạy.

Ví dụ log game:

```text
Turn 08 | Player O | Alpha-Beta | move=(4, 3) | score=-2230 | depth=2 | nodes=87 | time=0.030285s
```

Log benchmark nên có schema rõ ràng, không chỉ in ra console. Mỗi dòng CSV raw cần đủ để phân tích lại mà không cần chạy game:

```csv
case_name,depth,algorithm,ai_player,best_move,score,nodes_visited,elapsed_time_sec,board_size
```

Benchmark comparison CSV cần đủ để trả lời câu hỏi trong báo cáo:

```csv
case_name,depth,ai_player,same_best_move,same_score,minimax_nodes,alphabeta_nodes,node_reduction_percent,minimax_time_sec,alphabeta_time_sec,time_reduction_percent
```

---

## 13. Notebook `notebooks/benchmark_analysis.ipynb`

Notebook này là phần áp dụng có chọn lọc từ notebook tham khảo của repo `MonHauVD/Caro_AI`. Không cần làm phức tạp như repo mẫu. Chỉ cần phục vụ trực tiếp báo cáo Level 3.

### 13.1. Mục tiêu notebook

Notebook cần làm được các việc sau:

1. Đọc `source_code/results/benchmark_results.csv`.
2. Đọc `source_code/results/benchmark_comparison.csv` nếu có.
3. Hiển thị 5 dòng đầu để kiểm tra dữ liệu.
4. Tạo bảng thống kê theo `algorithm` và `depth`.
5. So sánh số node Minimax và Alpha-Beta.
6. So sánh thời gian chạy Minimax và Alpha-Beta.
7. Kiểm tra Alpha-Beta có chọn cùng nước đi với Minimax không.
8. Tính phần trăm giảm node.
9. Tính phần trăm giảm thời gian.
10. Vẽ biểu đồ đơn giản phục vụ báo cáo.
11. Tạo một bảng summary cuối cùng có thể copy vào báo cáo.

### 13.2. Cell đề xuất

#### Cell 1: Import thư viện và khai báo đường dẫn

```python
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path.cwd()
if ROOT.name == "notebooks":
    ROOT = ROOT.parent

raw_path = ROOT / "source_code" / "results" / "benchmark_results.csv"
comparison_path = ROOT / "source_code" / "results" / "benchmark_comparison.csv"

print(raw_path, raw_path.exists())
print(comparison_path, comparison_path.exists())
```

#### Cell 2: Đọc dữ liệu

```python
raw_df = pd.read_csv(raw_path)
comparison_df = pd.read_csv(comparison_path) if comparison_path.exists() else pd.DataFrame()
raw_df.head()
```

#### Cell 3: Thống kê tổng quan

```python
print("Total raw runs:", len(raw_df))
print(raw_df.groupby(["algorithm", "depth"])[["nodes_visited", "elapsed_time_sec"]].mean())
```

#### Cell 4: Bảng so sánh Minimax vs Alpha-Beta

```python
comparison_df[[
    "case_name",
    "depth",
    "same_best_move",
    "same_score",
    "minimax_nodes",
    "alphabeta_nodes",
    "node_reduction_percent",
    "minimax_time_sec",
    "alphabeta_time_sec",
    "time_reduction_percent",
]]
```

#### Cell 5: Tính trung bình giảm node và thời gian

```python
summary = comparison_df.groupby("depth").agg(
    avg_node_reduction_percent=("node_reduction_percent", "mean"),
    avg_time_reduction_percent=("time_reduction_percent", "mean"),
    same_move_rate=("same_best_move", "mean"),
    same_score_rate=("same_score", "mean"),
).reset_index()
summary
```

#### Cell 6: Biểu đồ nodes visited theo depth

```python
plot_df = raw_df.groupby(["depth", "algorithm"])["nodes_visited"].mean().reset_index()
for algorithm in plot_df["algorithm"].unique():
    sub = plot_df[plot_df["algorithm"] == algorithm]
    plt.plot(sub["depth"], sub["nodes_visited"], marker="o", label=algorithm)
plt.xlabel("Depth")
plt.ylabel("Average nodes visited")
plt.title("Average nodes visited by depth")
plt.legend()
plt.show()
```

#### Cell 7: Biểu đồ elapsed time theo depth

```python
plot_df = raw_df.groupby(["depth", "algorithm"])["elapsed_time_sec"].mean().reset_index()
for algorithm in plot_df["algorithm"].unique():
    sub = plot_df[plot_df["algorithm"] == algorithm]
    plt.plot(sub["depth"], sub["elapsed_time_sec"], marker="o", label=algorithm)
plt.xlabel("Depth")
plt.ylabel("Average elapsed time (s)")
plt.title("Average elapsed time by depth")
plt.legend()
plt.show()
```

#### Cell 8: Các case Alpha-Beta không chọn cùng move

```python
comparison_df[comparison_df["same_best_move"] == False]
```

Nếu có dòng khác move, không kết luận ngay là sai. Có thể có nhiều nước cùng score. Cần xem `same_score` và final board.

#### Cell 9: Xuất bảng summary cho báo cáo

```python
report_table = comparison_df.groupby("depth").agg(
    cases=("case_name", "count"),
    same_move_rate=("same_best_move", "mean"),
    avg_node_reduction_percent=("node_reduction_percent", "mean"),
    avg_time_reduction_percent=("time_reduction_percent", "mean"),
).reset_index()
report_table.to_csv(ROOT / "source_code" / "results" / "report_summary.csv", index=False)
report_table
```

### 13.3. Không cần áp dụng các phần quá nâng cao từ repo mẫu

Không cần làm trong bài này:

- Elo ranking.
- Beam search.
- Cython acceleration.
- Threat-space search.
- Lazy SMP.
- Difficulty preset phức tạp.
- Long-move spike analysis.
- AI tournament nhiều cấu hình.

Các phần trên chỉ là tham khảo. Đề bài yêu cầu trọng tâm là Minimax, Alpha-Beta, evaluator, depth limit, node count, elapsed time và phân tích kết quả.

---

## 14. Kiểm thử tối thiểu

Các nhóm test cần có:

- Thắng ngang với 4 quân liên tiếp.
- Thắng dọc với 4 quân liên tiếp.
- Thắng chéo chính với 4 quân liên tiếp.
- Thắng chéo phụ với 4 quân liên tiếp.
- Không cho đánh vào ô đã có quân.
- Hòa khi board đầy và không có người thắng.
- Evaluator đổi góc nhìn đúng theo `ai_player`.
- AI chọn nước thắng ngay khi có cơ hội.
- AI chặn đối thủ khi đối thủ có 3 quân liên tiếp.
- Minimax và Alpha-Beta cho score giống nhau trên cùng state, cùng depth, cùng evaluator.
- Alpha-Beta xét số node nhỏ hơn hoặc bằng Minimax trong các case phù hợp.
- AI vs AI không bị lệch logic do mặc định `O` luôn là AI.

Test đặc biệt cho evaluator:

```text
Cùng một board:
- evaluate(board, "X") phải là điểm từ góc nhìn X.
- evaluate(board, "O") phải là điểm từ góc nhìn O.
- Nếu board đang rất tốt cho X, điểm theo X phải dương và điểm theo O phải âm.
```

Test đặc biệt cho search:

```text
Nếu X có 3 quân liên tiếp và O là ai_player:
- Search của O nên ưu tiên nước chặn nếu không có nước thắng ngay.

Nếu O có 3 quân liên tiếp và O là ai_player:
- Search của O nên ưu tiên nước thắng nếu có thể tạo 4 quân.
```

---

## 15. Dữ liệu phục vụ báo cáo

Code cần tạo đủ dữ liệu để viết các phần sau:

- Mô tả bài toán cờ Caro.
- Luật chơi và điều kiện thắng.
- Cách biểu diễn trạng thái bàn cờ.
- Cách sinh nước đi hợp lệ.
- Cách kiểm tra trạng thái kết thúc.
- Thuật toán Minimax đã cài đặt.
- Thuật toán Alpha-Beta đã cài đặt.
- Hàm đánh giá trạng thái.
- Thiết kế các trạng thái thử nghiệm.
- Bảng kết quả thực nghiệm.
- Nhận xét số trạng thái đã xét và thời gian chạy.
- Nhận xét ảnh hưởng của độ sâu tìm kiếm.
- Ưu điểm và hạn chế của chương trình.
- Link repository GitHub.
- Tài liệu tham khảo và phần đã tham khảo từ repo mẫu.

Các câu hỏi bắt buộc cần trả lời bằng dữ liệu:

1. Alpha-Beta có chọn cùng nước đi với Minimax không?
2. Alpha-Beta giảm được bao nhiêu trạng thái so với Minimax?
3. Thời gian chạy thay đổi như thế nào khi tăng độ sâu?
4. Độ sâu tìm kiếm ảnh hưởng thế nào đến chất lượng nước đi?
5. Hàm đánh giá có ưu điểm gì và còn hạn chế gì?
6. Trường hợp nào AI chơi tốt?
7. Trường hợp nào AI chọn nước đi chưa hợp lý?
8. Nếu cải tiến tiếp, sẽ cải tiến phần nào?

Bảng quan trọng nhất trong báo cáo nên có dạng:

| State | Depth | Algorithm | Best move | Score | Nodes visited | Time |
|---|---:|---|---|---:|---:|---:|
| ai_must_block | 2 | Minimax | `(2, 6)` | 1200 | 8231 | 0.92s |
| ai_must_block | 2 | Alpha-Beta | `(2, 6)` | 1200 | 1940 | 0.21s |

Bảng tổng hợp nên có dạng:

| Depth | Same move rate | Avg node reduction | Avg time reduction |
|---:|---:|---:|---:|
| 1 | 100% | 20% | 10% |
| 2 | 100% | 60% | 50% |
| 3 | 100% | 80% | 70% |

Số liệu trên chỉ là ví dụ, code phải sinh số liệu thật.

---

## 16. Phân biệt rõ các loại đánh giá

Trong project này có hai loại đánh giá khác nhau:

### 16.1. Evaluator trong AI

File: `ai/evaluator.py`

Mục đích:

- Chấm điểm một trạng thái bàn cờ.
- Được Minimax và Alpha-Beta dùng trong search.
- Trả điểm theo góc nhìn `ai_player`.

Đây không phải là model học máy.

### 16.2. Benchmark analysis

File/module:

- `benchmark/benchmark_runner.py`
- `notebooks/benchmark_analysis.ipynb`

Mục đích:

- Đánh giá hiệu quả thuật toán.
- So sánh Minimax và Alpha-Beta về số node, thời gian, best move, score.
- Tạo bảng và biểu đồ để viết báo cáo.

Không được trộn hai khái niệm này.

---

## 17. Thứ tự triển khai khuyến nghị

1. Xây dựng constants.
2. Xây dựng board.
3. Xây dựng rules.
4. Xây dựng move generator.
5. Xây dựng evaluator theo `ai_player`.
6. Xây dựng base search và search result.
7. Xây dựng Minimax.
8. Xây dựng Alpha-Beta.
9. Xây dựng AI runner.
10. Xây dựng console UI.
11. Xây dựng game engine Human vs AI.
12. Xây dựng main menu.
13. Thêm AI vs AI nếu cần demo tự chơi.
14. Xây dựng test states.
15. Xây dựng result writer.
16. Xây dựng benchmark runner.
17. Xây dựng comparison CSV.
18. Xây dựng board writer nếu cần lưu board.
19. Xây dựng notebook benchmark analysis đơn giản.
20. Cập nhật README.
21. Chạy kiểm thử và benchmark.
22. Dùng CSV/notebook để viết báo cáo.

---

## 18. Definition of Done

Project được xem là hoàn thành khi:

- Chạy được chương trình trong `source_code`.
- Người chơi đấu được với AI bằng console.
- Có thể chọn AI dùng Minimax hoặc Alpha-Beta.
- AI hiển thị được nước đi, score, depth, nodes visited và elapsed time.
- Luật thắng đúng 4 quân liên tiếp.
- Không xét luật chặn hai đầu.
- Không đánh được vào ô đã có quân.
- Search và evaluator không hard-code `O` là AI.
- AI vs AI nếu có thì cả `X` và `O` đều có thể là `ai_player` đúng nghĩa.
- Benchmark chạy được trên ít nhất 5 states, khuyến nghị 6 states.
- Benchmark ghi được `benchmark_results.csv`.
- Benchmark ghi được `benchmark_comparison.csv` hoặc tạo được bảng so sánh tương đương.
- Minimax và Alpha-Beta được so sánh trên cùng state, cùng depth, cùng evaluator và cùng move generator.
- Có thể tính `node_reduction_percent` và `time_reduction_percent`.
- Có thể kiểm tra `same_best_move` và `same_score`.
- Có notebook hoặc script phân tích benchmark để tạo bảng phục vụ báo cáo.
- README hướng dẫn được cách chạy chương trình, benchmark và notebook.
- Code không copy nguyên repo mẫu.
- Báo cáo có kết quả chạy thử thật, không chỉ mô tả lý thuyết.

---

## 19. Ghi chú cho agent triển khai

Khi triển khai, agent cần ưu tiên thứ tự sau:

1. Đúng luật và đúng đề.
2. Code rõ module, dễ giải thích trong báo cáo.
3. Minimax và Alpha-Beta dùng chung interface.
4. Evaluator không hard-code `O`.
5. Benchmark công bằng.
6. Logging đủ dữ liệu.
7. Notebook phân tích đơn giản, không làm quá phức tạp.

Không cần cố làm AI quá mạnh. Một AI vừa đủ chơi được, có search depth, có evaluator, có Alpha-Beta giảm node rõ ràng và có báo cáo phân tích tốt là phù hợp với yêu cầu bài tập.
