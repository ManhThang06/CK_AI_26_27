# Task 2 - Tank Battle (Adversarial Search)

Game xe tăng theo lượt, điều khiển bằng Minimax, Alpha-Beta, Heuristic Minimax và
Heuristic Minimax + Alpha-Beta. Có giao diện PyGame và cơ chế nạp thuật toán của nhóm khác.

## 1. Cấu trúc thư mục

```
task2_tank/
  run_gui.py                chạy giao diện PyGame
  play_demo.py              chạy thử một ván trong console
  requirement.txt           thư viện cần cài (pygame)
  README.md
  maps/                     small.txt, medium.txt, full.txt
  engine/                   luật game: GameState, entities, GameMap, hằng số
  algorithms/
    adversarial.py          MinimaxSearch, AlphaBetaSearch
    heuristic_search.py     HeuristicMinimaxSearch, HeuristicAlphaBetaSearch
    heuristic_eval.py       hàm đánh giá Eval()
    agents.py               Agent, MinimaxAgent, AlphaBetaAgent, play_match
    scenarios.py            tạo trạng thái xuất phát (load_state, warmup)
  gui/
    app.py                  cửa sổ pygame: menu và màn hình chơi
    renderer.py             vẽ bàn chơi, tank, đạn, bảng thông tin
    game_controller.py      điều khiển ván chơi (không dùng pygame), bọc agent an toàn
    agent_registry.py       danh sách agent: Human, 4 thuật toán, plugin
  plugins/
    example_random_agent.py agent mẫu để nạp vào GUI
  experiments/
    compare_search.py       so sánh 4 cấu hình tìm kiếm (thời gian, số nút, cắt tỉa)
    tournament.py           đấu vòng tròn giữa các agent, kể cả plugin
    results/                kết quả đã chạy (CSV và log)
  tests/                    unit test
```

## 2. Cài đặt

Cần Python 3.8+.

```
pip install -r task2_tank/requirement.txt
```

Mọi lệnh bên dưới chạy từ thư mục **chứa** `task2_tank`.

## 3. Chạy

| Mục đích | Lệnh |
|---|---|
| Giao diện PyGame | `python task2_tank/run_gui.py` |
| Một ván trong console | `python -m task2_tank.play_demo --map small --horizon 2` |
| Thí nghiệm so sánh 4 cấu hình | `python -m task2_tank.experiments.compare_search` |
| Đấu vòng tròn các agent | `python -m task2_tank.experiments.tournament --depth 2` |
| Unit test | `python -m unittest discover -s task2_tank/tests -t .` |

(Chỉ giao diện cần pygame; phần còn lại chạy được không cần pygame.)

## 4. Luật game (theo đề)

- Bản đồ lưới, mỗi bên có 1 tank và 1 base. HP ban đầu: tank 6, base 9, tường 3; mỗi phát bắn trừ 1 HP.
- Tank có 6 hành động: `MOVE_UP, MOVE_DOWN, MOVE_LEFT, MOVE_RIGHT, FIRE, STAY`; mỗi lượt đi tối đa 1 ô.
- Đạn bay 3 ô mỗi cycle theo hướng nòng, kiểm tra va chạm sau từng ô và dừng ngay khi trúng tường, tank hoặc base.
- Game kết thúc khi một tank hoặc một base bị phá. Bên còn lại thắng. Nếu hết 100 cycle mà chưa ai thua thì hòa.

Cách engine mô hình hóa (`engine/game_state.py`):
- Một cycle gồm 2 ply: P1 (MAX) chọn, rồi P2 (MIN) chọn khi đã biết hành động của P1, sau đó engine xử lý cả cycle (tank di chuyển, bắn đạn mới, đạn bay 3 ô).
- Mỗi tank chỉ có tối đa một viên đạn đang bay; FIRE khi đạn cũ còn bay bị bỏ qua.
- Hai tank cùng đi vào một ô: ưu tiên luân phiên theo cycle (cycle chẵn P1, lẻ P2), bên còn lại đứng nguyên. Nếu đích là ô tank đang đứng yên hoặc hai tank đổi chỗ thì cả hai ở lại.
- Tank bước vào ô đang chứa đạn bay tới thì bị đạn trúng ngay (đạn không xuyên qua tank).

## 5. Thuật toán

| Cấu hình | Lớp | Ghi chú |
|---|---|---|
| Minimax | `MinimaxSearch` | duyệt toàn bộ cây tới horizon, không cắt tỉa |
| Alpha-Beta | `AlphaBetaSearch` | cùng giá trị gốc như Minimax, bỏ nhánh không ảnh hưởng quyết định |
| Heuristic Minimax | `HeuristicMinimaxSearch` | giới hạn độ sâu, nút lá đánh giá bằng `Eval()` |
| Heuristic Alpha-Beta | `HeuristicAlphaBetaSearch` | như trên có cắt tỉa Alpha-Beta |

- Độ sâu tính bằng số cycle nhìn trước (1 cycle = 2 ply, mỗi nút có 6 nhánh).
- Minimax và Alpha-Beta thuần không thể duyệt tới nút kết thúc thật (tối đa 100 cycle), nên cắt ở horizon và coi như chưa phân thắng thua. Với tùy chọn `horizon_score`, nút bị cắt được tính bằng chênh lệch HP tank + base chia 100, luôn nhỏ hơn giá trị thắng/thua thật.
- `Eval()` (`heuristic_eval.py`) gồm: chênh lệch HP base và tank, chi phí đường đi tới vị trí bắn được base địch (Dijkstra, tường tính theo HP), tank đang ngắm trúng địch, đạn đang bay, độ linh hoạt di chuyển, tường quanh base, phạt đi lòng vòng.
- Tối ưu để chạy realtime: sắp xếp nước đi (FIRE trúng địch trước), bỏ nước vô tác dụng, bỏ nước bước vào đường đạn chắc chắn trúng, cache đường đi, iterative deepening theo `time_limit`.
- Tùy chọn cho agent chơi trong GUI: `randomize` chọn ngẫu nhiên có seed giữa các nước bằng điểm (nếu không, Minimax thuần luôn lấy nước đầu tiên và tank đâm tường mãi); mặc định tắt để thí nghiệm tất định.

## 6. Thí nghiệm

### 6.1 So sánh 4 cấu hình (`experiments/compare_search.py`)

Cùng điều kiện cho cả 4 cấu hình: 3 map x 4 trạng thái xuất phát (đầu ván và giữa ván, seed cố định) = 12 kịch bản, HP chuẩn, cùng độ sâu 1 đến 3 cycle, tắt move ordering, lọc nước và ngẫu nhiên. Chỉ số: thời gian, số nút sinh ra, số lần cắt tỉa, số nhánh bị bỏ, số lần gọi `Eval()`. Có kiểm tra Alpha-Beta cho cùng giá trị gốc như Minimax tương ứng.

Kết quả trung bình (xem `experiments/results/`):

| Độ sâu | Thuật toán | Thời gian (s) | Số nút | Cắt tỉa | Gọi Eval |
|---|---|---|---|---|---|
| 1 | Minimax | 0.0003 | 42 | 0 | 0 |
| 1 | Alpha-Beta | 0.0001 | 17 | 5 | 0 |
| 1 | Heuristic Minimax | 0.0025 | 42 | 0 | 36 |
| 1 | Heuristic Alpha-Beta | 0.0005 | 22 | 4 | 16 |
| 2 | Minimax | 0.0084 | 1554 | 0 | 0 |
| 2 | Alpha-Beta | 0.0007 | 129 | 45 | 0 |
| 2 | Heuristic Minimax | 0.0417 | 1554 | 0 | 1296 |
| 2 | Heuristic Alpha-Beta | 0.0042 | 216 | 54 | 139 |
| 3 | Minimax | 0.2904 | 55986 | 0 | 0 |
| 3 | Alpha-Beta | 0.0040 | 812 | 295 | 0 |
| 3 | Heuristic Minimax | 1.2802 | 55986 | 0 | 46656 |
| 3 | Heuristic Alpha-Beta | 0.0354 | 1892 | 508 | 1189 |

Nhận xét: số nút của Minimax tăng gấp khoảng 36 lần mỗi cycle (6^2), còn Alpha-Beta tăng chậm hơn nhiều; ở độ sâu 3, Alpha-Beta sinh ít hơn Minimax khoảng 69 lần số nút. Bản Heuristic chậm hơn bản thuần cùng số nút vì mỗi lá phải gọi `Eval()`, nhưng chọn nước đi tốt hơn (xem 6.2).

### 6.2 Đấu vòng tròn (`experiments/tournament.py`)

Mỗi cặp agent đấu trên 3 map và đổi bên (HP chuẩn, độ sâu 2). Tournament cũng tự đưa các plugin trong `plugins/` vào giải. Kết quả ví dụ (W/D/L trên 24 ván mỗi agent; plugin ngẫu nhiên không seed nên số liệu có thể lệch nhẹ giữa các lần chạy):

| Agent | W | D | L | ms / nước |
|---|---|---|---|---|
| Heuristic Minimax | 19 | 4 | 1 | 24.8 |
| Heuristic Alpha-Beta | 19 | 4 | 1 | 4.5 |
| Alpha-Beta | 4 | 7 | 13 | 1.5 |
| Minimax | 4 | 7 | 13 | 4.9 |
| Random (plugin) | 0 | 6 | 18 | 0.0 |

Hai bản Heuristic thắng áp đảo; cùng chất lượng chơi nhưng bản có Alpha-Beta nhanh hơn khoảng 5 lần.

## 7. Giao diện

**Menu:** bấm nửa trái hoặc nửa phải của một dòng (hoặc phím mũi tên) để đổi giá trị, Enter để bắt đầu.

| Dòng | Lựa chọn |
|---|---|
| Map | small, medium, full |
| Player 1 (green) / Player 2 (orange) | Human, Minimax, Alpha-Beta, Heuristic Minimax, Heuristic Alpha-Beta và các plugin |
| Depth | 1 đến 4 cycle nhìn trước (Minimax thuần tối đa 3 vì quá chậm hơn) |

Mỗi tank chọn thuật toán và độ sâu riêng nên chơi người với máy, máy với máy, hoặc hai thuật toán cùng loại đều được.

**Trong ván:**

| Phím | Tác dụng |
|---|---|
| P | tạm dừng / tiếp tục |
| N | chạy từng cycle |
| + / - | chạy nhanh / chậm |
| R | chơi lại ván |
| ESC | về menu |
| P1: W A S D, SPACE bắn, Q đứng yên | điều khiển tay P1 |
| P2: phím mũi tên, ENTER bắn, Right Shift đứng yên | điều khiển tay P2 |

Thanh thông tin hiển thị HP tank/base, thuật toán, thời gian suy nghĩ, số nút đã sinh và hành động gần nhất của mỗi bên. Thuật toán chạy trong thread nền nên cửa sổ không bị đứng.

## 8. Nạp thuật toán của nhóm khác (plugins)

1. Chép file `.py` của nhóm khác vào `task2_tank/plugins/`.
2. Mở GUI (hoặc bấm **Reload plugins**, phím F5, ở menu). Agent xuất hiện trong danh sách Player 1 / Player 2 với đuôi `[plugin]`.
3. Chọn agent đó cho một bên, thuật toán của nhóm mình cho bên kia rồi Start.

File plugin cần một trong hai thứ:
- hàm `create_agent()` trả về đối tượng agent; hoặc
- một lớp có phương thức `choose_action(state)`.

Hợp đồng:
- `choose_action(state)` trả về một `Action` của engine (`MOVE_UP, MOVE_DOWN, MOVE_LEFT, MOVE_RIGHT, FIRE, STAY`).
- `state.player()` cho biết đang chơi bên nào (0 = P1, 1 = P2), nên agent phải chơi được cả hai bên.
- Thuộc tính `name` (tùy chọn) là tên hiển thị.
- File có tên bắt đầu bằng `_` bị bỏ qua.

Plugin hỏng khi nạp sẽ được báo lỗi ở menu mà không làm sập GUI. Nếu agent ném lỗi hoặc trả hành động không hợp lệ giữa ván, tank đứng yên (STAY) và lỗi hiện đỏ trong bảng thông tin. Xem mẫu ở `plugins/example_random_agent.py`.
