# Kim chỉ nam xây dựng pipeline Caro AI

Tài liệu này dùng làm bối cảnh kỹ thuật cho quá trình xây dựng project Caro AI. Nội dung bám theo yêu cầu trong `De_so_1.pdf`, tập trung vào cấu trúc dự án, các module cần có, các hàm cần xây dựng và luồng hoạt động của chương trình.

## 1. Bối cảnh bài toán

Project cần xây dựng một chương trình chơi cờ Caro giữa người chơi và máy tính. Chương trình có thể chạy bằng console, không bắt buộc có giao diện đồ họa.

Các yêu cầu chính:

- Bàn cờ có kích thước tối thiểu 9x9.
- Người chơi có thể dùng quân `X`.
- Máy có thể dùng quân `O`.
- Ô trống được biểu diễn bằng dấu chấm `.`.
- Hai bên đánh luân phiên.
- Không được đánh vào ô đã có quân.
- Người thắng là người có 4 quân liên tiếp theo hàng ngang, hàng dọc, đường chéo chính hoặc đường chéo phụ.
- Không xét luật chặn hai đầu.
- Nếu bàn cờ đầy và không có người thắng thì kết quả là hòa.

Project cần hoàn thành ba mức chính:

- Level 1: AI chơi Caro bằng Minimax có giới hạn độ sâu.
- Level 2: Cải tiến bằng Alpha-Beta pruning.
- Level 3: Benchmark và phân tích hiệu quả Minimax so với Alpha-Beta trên nhiều trạng thái bàn cờ.

## 2. Nguyên tắc thiết kế

Pipeline phải dùng chung cho Minimax và Alpha-Beta. Khi chuyển thuật toán, chỉ thay module tìm kiếm, không thay luật chơi, board, evaluator, move generator hoặc benchmark.

Các nguyên tắc cần giữ:

- Ưu tiên đúng đề hơn độ mạnh của AI.
- Luật thắng luôn là 4 quân liên tiếp.
- Không dùng luật Gomoku 5 quân.
- Không hard-code `O` luôn là AI trong evaluator và search.
- Mỗi searcher phải biết nó đang tìm nước đi cho player nào.
- Minimax và Alpha-Beta phải dùng cùng evaluator khi so sánh.
- Minimax và Alpha-Beta phải dùng cùng độ sâu khi benchmark.
- Benchmark phải chạy hai thuật toán trên cùng trạng thái bàn cờ.
- Candidate moves và move ordering chỉ là tối ưu hợp lệ, không được làm sai khái niệm nước đi hợp lệ.

## 3. Luồng hoạt động tổng quát

Luồng chơi Human vs AI:

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

Luồng benchmark:

1. Tải danh sách trạng thái kiểm thử.
2. Với mỗi trạng thái, tạo lại board tương ứng.
3. Chạy Minimax ở một độ sâu xác định.
4. Chạy Alpha-Beta ở cùng trạng thái và cùng độ sâu.
5. Ghi best move, score, số node đã xét và thời gian chạy.
6. Lặp lại với các độ sâu khác nếu có.
7. Ghi toàn bộ kết quả ra CSV.
8. Dùng CSV để viết phần phân tích trong báo cáo.

## 4. Cấu trúc dự án đề xuất

- `source_code/`
  - `main.py`: entry point của chương trình.
  - `config.py`: cấu hình mặc định.
  - `core/`: xử lý board, luật chơi và sinh nước đi.
  - `ai/`: evaluator, Minimax, Alpha-Beta và interface search chung.
  - `engine/`: điều phối game và tạo AI runner.
  - `ui/`: giao diện console.
  - `benchmark/`: trạng thái kiểm thử, runner và writer kết quả.
  - `results/`: chứa file benchmark CSV.
- `README.md`: hướng dẫn chạy chương trình.
- `requirements.txt`: dependency nếu có.
- `docs/pipeline_modules.md`: tài liệu định hướng triển khai.

## 5. Module `core`

Nhóm `core` chứa các thành phần nền tảng của trò chơi. Những module này không phụ thuộc vào Minimax hay Alpha-Beta.

### 5.1. `core/constants.py`

Mục đích:

- Tập trung các hằng số của game.
- Tránh lặp magic number hoặc hard-code ký hiệu quân cờ ở nhiều nơi.

Cần có:

- Hằng số ô trống.
- Hằng số người chơi `X`.
- Hằng số người chơi `O`.
- Hằng số độ dài thắng là 4.
- Hằng số kích thước board mặc định là 9.
- Danh sách 4 hướng kiểm tra thắng: ngang, dọc, chéo chính, chéo phụ.

### 5.2. `core/board.py`

Mục đích:

- Quản lý trạng thái bàn cờ.
- Cung cấp thao tác đặt quân, hoàn tác và truy vấn board.

Cần xây dựng class `Board`.

Các hàm cần có:

- `__init__`: tạo board với kích thước tối thiểu 9x9.
- `is_inside`: kiểm tra tọa độ có nằm trong bàn cờ không.
- `is_empty_cell`: kiểm tra một ô có trống không.
- `place_move`: đặt quân nếu nước đi hợp lệ.
- `undo_move`: hoàn tác nước đi.
- `get_empty_cells`: lấy danh sách ô trống.
- `is_full`: kiểm tra board đã đầy chưa.
- `clone`: tạo bản sao board nếu cần.
- `display` hoặc `to_string`: hiển thị hoặc chuyển board thành chuỗi.

Yêu cầu quan trọng:

- Không cho đặt quân ngoài bàn cờ.
- Không cho đặt quân vào ô đã có quân.
- Search nên dùng đặt quân rồi undo để tránh clone quá nhiều.

### 5.3. `core/rules.py`

Mục đích:

- Xử lý luật thắng, hòa và trạng thái kết thúc.

Các hàm cần có:

- `check_winner`: kiểm tra một player đã thắng chưa.
- `check_draw`: kiểm tra bàn cờ hòa chưa.
- `get_game_status`: trả về trạng thái hiện tại của ván đấu.

Trạng thái game nên có:

- Đang chơi.
- `X` thắng.
- `O` thắng.
- Hòa.

Yêu cầu quan trọng:

- Chỉ cần 4 quân liên tiếp là thắng.
- Kiểm tra đủ 4 hướng.
- Không xét luật chặn hai đầu.

### 5.4. `core/move_generator.py`

Mục đích:

- Sinh danh sách nước đi hợp lệ cho thuật toán tìm kiếm.
- Có thể giảm không gian tìm kiếm bằng candidate moves.

Các hàm cần có:

- `generate_legal_moves`: trả về toàn bộ ô trống.
- `generate_candidate_moves`: trả về các ô trống gần những quân đã đánh.
- Hàm hỗ trợ sắp xếp nước đi nếu cần.

Yêu cầu quan trọng:

- Nếu board trống, candidate move nên là ô trung tâm.
- Nếu board đã có quân, candidate moves chỉ chọn các ô trống gần quân đã đánh.
- Nếu có lọc hoặc sắp xếp candidate moves, phải dùng giống nhau cho Minimax và Alpha-Beta trong benchmark.
- Nếu có move ordering, cần ghi rõ trong README hoặc báo cáo.

## 6. Module `ai`

Nhóm `ai` chứa evaluator và các thuật toán tìm kiếm. Tất cả thuật toán phải dùng chung board, rules và move generator.

### 6.1. `ai/evaluator.py`

Mục đích:

- Đánh giá trạng thái bàn cờ khi chưa đạt terminal state hoặc khi đã hết độ sâu tìm kiếm.
- Trả điểm theo góc nhìn của `ai_player`.

Cần xây dựng class `Evaluator`.

Các hàm cần có:

- `evaluate`: nhận board và `ai_player`, trả về điểm đánh giá.
- Hàm phụ để đánh giá chuỗi quân theo từng hướng.
- Hàm phụ để xác định đối thủ của `ai_player`.

Tiêu chí đánh giá gợi ý:

- AI có 4 quân liên tiếp: điểm rất lớn.
- Đối thủ có 4 quân liên tiếp: điểm rất âm.
- AI có 3 quân liên tiếp: điểm cao.
- Đối thủ có 3 quân liên tiếp: điểm âm mạnh để ưu tiên chặn.
- AI có 2 quân liên tiếp: điểm dương nhỏ.
- Đối thủ có 2 quân liên tiếp: điểm âm nhỏ.

Yêu cầu quan trọng:

- Không gọi đây là machine learning model.
- Không hard-code `O` là AI.
- Điểm tốt cho `ai_player` phải là điểm dương.
- Điểm tốt cho đối thủ phải là điểm âm.

### 6.2. `ai/base_search.py`

Mục đích:

- Định nghĩa kết quả search dùng chung.
- Định nghĩa interface chung cho Minimax và Alpha-Beta.
- Chứa helper dùng chung nếu cần.

Cần có dataclass hoặc cấu trúc dữ liệu `SearchResult`.

Thông tin trong `SearchResult`:

- `best_move`
- `score`
- `depth`
- `nodes_visited`
- `elapsed_time`
- `algorithm`
- `player`

Các hàm cần có:

- `search`: interface chung cho các thuật toán.
- `get_opponent`: lấy đối thủ của một player.
- `terminal_score`: tính điểm kết thúc theo góc nhìn của `ai_player`.

### 6.3. `ai/minimax.py`

Mục đích:

- Cài đặt thuật toán Minimax cho Level 1.

Cần xây dựng class `MinimaxSearch`.

Các hàm cần có:

- `search`: hàm public để AI tìm nước đi.
- `_minimax`: hàm đệ quy xử lý MAX/MIN.

Yêu cầu thuật toán:

- Nếu trạng thái là thắng, thua hoặc hòa, trả về điểm kết thúc.
- Nếu đạt giới hạn độ sâu, gọi evaluator.
- Nếu là lượt của `ai_player`, chọn giá trị lớn nhất.
- Nếu là lượt của đối thủ, chọn giá trị nhỏ nhất.
- Trả về nước đi tốt nhất và score tương ứng.
- Đếm số trạng thái đã xét.
- Đo thời gian chạy.

### 6.4. `ai/alpha_beta.py`

Mục đích:

- Cài đặt Alpha-Beta pruning cho Level 2.

Cần xây dựng class `AlphaBetaSearch`.

Các hàm cần có:

- `search`: hàm public để AI tìm nước đi.
- `_alpha_beta`: hàm đệ quy có alpha và beta.

Yêu cầu thuật toán:

- Dùng cùng evaluator với Minimax.
- Dùng cùng move generator với Minimax khi benchmark.
- Dùng cùng depth với Minimax khi so sánh.
- Cập nhật alpha ở nhánh MAX.
- Cập nhật beta ở nhánh MIN.
- Cắt nhánh khi beta nhỏ hơn hoặc bằng alpha.
- Trả về cùng kiểu `SearchResult` như Minimax.

## 7. Module `engine`

Nhóm `engine` điều phối giữa UI, board, rules và AI.

### 7.1. `engine/ai_runner.py`

Mục đích:

- Tạo đúng searcher theo chế độ người dùng chọn.
- Giúp game engine không phụ thuộc trực tiếp vào class cụ thể.

Các hàm cần có:

- `create_searcher`: nhận tên thuật toán và trả về Minimax hoặc Alpha-Beta searcher.
- Hàm chuẩn hóa tên thuật toán nếu cần.

Các mode cần hỗ trợ:

- `minimax`
- `alphabeta`
- `alpha-beta`
- `alpha_beta`

### 7.2. `engine/game_engine.py`

Mục đích:

- Điều phối ván chơi Human vs AI.
- Quản lý lượt chơi.
- Gọi searcher để AI chọn nước.
- Kiểm tra trạng thái kết thúc sau mỗi lượt.

Các hàm cần có:

- Hàm khởi tạo game.
- Hàm chạy Human vs AI.
- Hàm xử lý lượt người chơi.
- Hàm xử lý lượt AI.
- Hàm kiểm tra kết thúc ván.
- Hàm log kết quả AI.

Yêu cầu quan trọng:

- Human vs AI là mode chính.
- Người chơi mặc định là `X`.
- AI mặc định là `O`.
- AI có thể dùng Minimax hoặc Alpha-Beta.
- Sau lượt AI phải hiển thị nước đi, score, depth, nodes visited và elapsed time.

AI vs AI nếu có chỉ là mode mở rộng, không dùng làm benchmark chính.

## 8. Module `ui`

### 8.1. `ui/console_ui.py`

Mục đích:

- Cung cấp giao diện console đơn giản.
- Đọc input an toàn.
- In board và thông báo trạng thái game.

Các hàm cần có:

- `show_main_menu`: hiển thị menu chính.
- `read_board_size`: đọc kích thước board.
- `read_ai_mode`: đọc thuật toán AI.
- `read_depth`: đọc độ sâu tìm kiếm.
- `read_player_move`: đọc nước đi người chơi.
- `print_board`: in bàn cờ.
- `print_ai_result`: in kết quả tìm kiếm của AI.
- `print_game_status`: in kết quả thắng, thua hoặc hòa.

Yêu cầu xử lý input:

- Người dùng nhập không phải số.
- Người dùng nhập tọa độ ngoài board.
- Người dùng nhập vào ô đã có quân.
- Người dùng nhập board size nhỏ hơn 9.
- Người dùng nhập thuật toán không hợp lệ.

## 9. Module `benchmark`

Nhóm `benchmark` phục vụ Level 3 và báo cáo thực nghiệm.

### 9.1. `benchmark/test_states.py`

Mục đích:

- Chuẩn bị các trạng thái bàn cờ để kiểm thử Minimax và Alpha-Beta.
- Đảm bảo hai thuật toán chạy trên cùng dữ liệu.

Cần có ít nhất 5 trạng thái:

- Trạng thái đầu ván.
- Trạng thái đầu hoặc gần đầu ván.
- Trạng thái giữa ván.
- Trạng thái AI có thể thắng ngay.
- Trạng thái người chơi sắp thắng, AI cần chặn.
- Trạng thái hai bên đều có cơ hội tấn công hoặc có nhiều nước đi hợp lệ.

Các hàm cần có:

- `board_from_strings`: tạo board từ danh sách chuỗi.
- Hàm validate trạng thái nếu cần.

### 9.2. `benchmark/benchmark_runner.py`

Mục đích:

- Chạy thực nghiệm so sánh Minimax và Alpha-Beta.
- Thu thập dữ liệu cho báo cáo.

Các hàm cần có:

- `run_benchmark`: chạy toàn bộ benchmark.
- `run_single_case`: chạy một thuật toán trên một trạng thái cụ thể.
- Hàm tạo evaluator và searcher dùng chung.
- Hàm tổng hợp kết quả.

Mỗi dòng kết quả cần có:

- Tên trạng thái.
- Độ sâu.
- Thuật toán.
- Player đang được AI tối ưu.
- Best move.
- Score.
- Số node đã xét.
- Thời gian chạy.
- Kích thước board.

Yêu cầu quan trọng:

- Minimax và Alpha-Beta phải chạy trên cùng state.
- Minimax và Alpha-Beta phải dùng cùng depth.
- Minimax và Alpha-Beta phải dùng cùng evaluator.
- Minimax và Alpha-Beta phải dùng cùng move generator.

### 9.3. `benchmark/result_writer.py`

Mục đích:

- Ghi kết quả benchmark ra file CSV.
- Tạo thư mục output nếu chưa có.

Các hàm cần có:

- `write_results`: ghi danh sách kết quả ra CSV.
- Hàm tạo thư mục `results` nếu cần.
- Hàm in summary ngắn nếu cần.

Output mặc định:

- `source_code/results/benchmark_results.csv`

## 10. `main.py`

Mục đích:

- Là entry point của chương trình.
- Kết nối UI, game engine và benchmark runner.

Luồng chính:

1. Hiển thị menu.
2. Người dùng chọn Human vs AI hoặc benchmark.
3. Nếu chọn Human vs AI, đọc board size, thuật toán và depth rồi chạy game.
4. Nếu chọn benchmark, chạy benchmark runner và ghi CSV.
5. In thông báo kết quả.

Menu tối thiểu:

- Human X vs AI O.
- Benchmark Minimax vs Alpha-Beta.

AI vs AI chỉ thêm nếu còn thời gian và không làm ảnh hưởng phần chính.

## 11. `README.md`

README cần phục vụ nộp bài và chạy chương trình.

Nội dung cần có:

- Tên project.
- Mô tả ngắn bài toán.
- Yêu cầu môi trường.
- Cách cài dependencies.
- Cách chạy Human vs AI.
- Cách chạy benchmark.
- Vị trí file kết quả benchmark.
- Mô tả ngắn Minimax.
- Mô tả ngắn Alpha-Beta.
- Mô tả ngắn evaluator.
- Ghi chú nếu có dùng candidate moves hoặc move ordering.

## 12. Logging

Mỗi lần AI chọn nước đi, chương trình cần ghi hoặc in:

- Thuật toán đang dùng.
- Player của AI.
- Nước đi được chọn.
- Score.
- Depth.
- Số trạng thái đã xét.
- Thời gian chạy.

Thông tin logging này cần xuất hiện trong game loop và trong benchmark CSV.

## 13. Kiểm thử tối thiểu

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

## 14. Dữ liệu phục vụ báo cáo

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

## 15. Thứ tự triển khai khuyến nghị

1. Xây dựng constants.
2. Xây dựng board.
3. Xây dựng rules.
4. Xây dựng move generator.
5. Xây dựng evaluator.
6. Xây dựng base search và search result.
7. Xây dựng Minimax.
8. Xây dựng Alpha-Beta.
9. Xây dựng AI runner.
10. Xây dựng console UI.
11. Xây dựng game engine.
12. Xây dựng main menu.
13. Xây dựng test states.
14. Xây dựng result writer.
15. Xây dựng benchmark runner.
16. Cập nhật README.
17. Chạy kiểm thử và benchmark.

## 16. Definition of Done

Project được xem là hoàn thành khi:

- Chạy được chương trình trong `source_code`.
- Người chơi đấu được với AI bằng console.
- Có thể chọn AI dùng Minimax hoặc Alpha-Beta.
- AI hiển thị được nước đi, score, depth, nodes visited và elapsed time.
- Luật thắng đúng 4 quân liên tiếp.
- Không xét luật chặn hai đầu.
- Không đánh được vào ô đã có quân.
- Benchmark chạy được trên ít nhất 5 states.
- Benchmark ghi được CSV.
- Minimax và Alpha-Beta được so sánh trên cùng state, cùng depth, cùng evaluator và cùng move generator.
- README hướng dẫn được cách chạy chương trình và benchmark.
- Code không hard-code `O` là AI trong search hoặc evaluator.
- Code không copy nguyên repo mẫu.
