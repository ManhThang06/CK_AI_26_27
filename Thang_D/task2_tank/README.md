# Task 2 - Tank Battle (Adversarial Search + GUI PyGame)

Game xe tăng theo lượt, điều khiển bằng Minimax, Alpha-Beta, Heuristic Minimax và Heuristic Alpha-Beta.
Có giao diện PyGame để chọn thuật toán cho từng xe tăng, chơi bằng tay, và nạp agent của nhóm khác.

## 1. Cấu trúc thư mục

```
Thang_D/                      <- thư mục chung của nhóm (chạy lệnh từ đây hoặc từ trong task2_tank)
  task2_tank/
    run_gui.py                [MỚI] chạy GUI
    requirement.txt           [MỚI] pygame>=2.5
    README.md                 [MỚI] file này
    engine/                   engine của team (không sửa)
    maps/                     small.txt, medium.txt, full.txt
    algorithms/
      adversarial.py          MinimaxSearch, AlphaBetaSearch
      heuristic_search.py     HeuristicMinimaxSearch, HeuristicAlphaBetaSearch
      heuristic_eval.py       hàm đánh giá Eval()
      agents.py               Agent, MinimaxAgent, AlphaBetaAgent, play_match
      scenarios.py            tạo trạng thái xuất phát
    gui/                      [MỚI] toàn bộ phần giao diện
      __init__.py
      app.py                  cửa sổ pygame: menu và màn hình chơi
      renderer.py             vẽ bàn chơi, tank, đạn, bảng thông tin
      game_controller.py      điều khiển ván chơi (không dùng pygame), bọc agent an toàn
      agent_registry.py       danh sách agent: Human, 4 thuật toán, plugin
    plugins/                  [MỚI] đặt agent của nhóm khác vào đây
      example_random_agent.py ví dụ agent ngẫu nhiên
    experiments/  tests/  tools/  play_demo.py   giữ nguyên
```

## 2. Cách đặt file vào thư mục chung

Giải nén gói GUI rồi chép vào `task2_tank/` đã có:

| File/thư mục mới | Đặt ở |
|---|---|
| `gui/` (5 file) | `task2_tank/gui/` |
| `plugins/example_random_agent.py` | `task2_tank/plugins/` |
| `run_gui.py` | `task2_tank/run_gui.py` |
| `requirement.txt` | `task2_tank/requirement.txt` |
| `README.md` | `task2_tank/README.md` (thay README cũ) |

Không cần sửa file nào của `engine/` hay `algorithms/`.

## 3. Cài đặt và chạy

```
pip install -r task2_tank/requirement.txt
python task2_tank/run_gui.py
```

(hoặc `cd task2_tank` rồi `python run_gui.py`). Cần Python 3.8+ và pygame 2.x.

Các phần còn lại không cần pygame:
```
python -m unittest discover -s task2_tank/tests -t .
python -m task2_tank.experiments.compare_search
```
(lệnh chạy từ thư mục chứa `task2_tank`).

## 4. Dùng GUI

**Menu:** bấm nửa trái hoặc nửa phải của một dòng (hoặc phím mũi tên) để đổi giá trị, Enter để bắt đầu.

| Dòng | Lựa chọn |
|---|---|
| Mode | **Same algorithm for both tanks** (mặc định: chọn 1 trong 4 thuật toán cho cả hai tank) hoặc Different algorithm per tank (mỗi tank một thuật toán, để so sánh hai thuật toán đấu nhau hoặc đấu với plugin) |
| Map | small, medium, full |
| HP preset | Standard 6/9/3 (đúng đề), Medium 3/3/2, Low 1/1/1 |
| Algorithm (chế độ Same) hoặc Player 1 / Player 2 (chế độ Different) | Human, Minimax, Alpha-Beta, Heuristic Minimax, Heuristic Alpha-Beta, và các plugin |
| Depth | 1 đến 4 cycle nhìn trước (Minimax thuần tối đa 3 vì quá chậm hơn) |

Lưu ý:
- Minimax và Alpha-Beta thuần chỉ thấy thắng/thua trong phạm vi depth, nên với HP chuẩn chúng thường đánh giá mọi nước là hòa. Hãy chọn HP Low để thấy chúng chơi có mục đích. Hai bản Heuristic chơi tốt ở mọi mức HP.
- Ở chế độ Same, hai tank dùng cùng thuật toán và cùng độ sâu nhưng mỗi tank có agent riêng. Mỗi agent tự mô phỏng cả MAX lẫn MIN trong cây tìm kiếm của nó: tank P1 coi mình là MAX, tank P2 coi mình là MIN.
- Chế độ Different cần khi đấu agent của nhóm khác (yêu cầu 3 của đề).
- Mỗi bên có thể là Human, nên chơi người với máy hoặc máy với máy đều được.

**Trong ván:**

| Phím | Tác dụng |
|---|---|
| P | tạm dừng / tiếp tục |
| N | chạy từng cycle |
| + / - | chạy nhanh / chậm |
| R | chơi lại ván |
| ESC | về menu |
| P1 (xanh): W A S D, SPACE bắn, Q đứng yên | |
| P2 (đỏ): phím mũi tên, ENTER bắn, Right Shift đứng yên | |

Bảng bên phải hiển thị HP tank/base, hành động gần nhất, thời gian suy nghĩ và số nút đã sinh của mỗi thuật toán, cùng log các cycle gần nhất. Hiệu ứng nổ xuất hiện ở nơi đạn trúng.

## 5. Nạp thuật toán của nhóm khác (plugins)

1. Chép file `.py` của nhóm khác vào `task2_tank/plugins/`.
2. Mở GUI (hoặc bấm **Reload plugins**, phím F5, ở menu). Agent xuất hiện trong danh sách Player 1 / Player 2 với đuôi `[plugin]`.
3. Chọn agent đó cho một bên, chọn thuật toán của nhóm mình cho bên kia rồi Start.

File plugin cần một trong hai thứ:
- hàm `create_agent()` trả về đối tượng agent; hoặc
- một lớp có phương thức `choose_action(state)`.

Hợp đồng:
- `choose_action(state)` trả về một `Action` của engine (`MOVE_UP, MOVE_DOWN, MOVE_LEFT, MOVE_RIGHT, FIRE, STAY`).
- `state.player()` cho biết đang chơi bên nào (0 = P1, 1 = P2), nên agent phải chơi được cả hai bên.
- Thuộc tính `name` (tùy chọn) là tên hiển thị.
- File có tên bắt đầu bằng `_` bị bỏ qua.

Plugin hỏng khi nạp sẽ được báo lỗi ở menu mà không làm sập GUI. Nếu agent ném lỗi hoặc trả hành động không hợp lệ giữa ván, tank đứng yên (STAY) và lỗi hiện đỏ trong bảng thông tin.

Mẫu tối thiểu:
```python
import random

class MyAgent:
    name = "My agent"
    def choose_action(self, state):
        return random.choice(state.legal_actions())
```

## 6. Ghi chú kỹ thuật

- `game_controller.py` không dùng pygame nên test được riêng. Thuật toán chạy trong thread nền để cửa sổ không bị đứng.
- Mỗi cycle gồm 2 ply: P1 chọn, rồi P2 chọn khi đã biết hành động của P1, sau đó engine xử lý cả cycle. Đây là cách mô hình hóa của engine nên P2 có lợi thế thông tin nhẹ.
- Hai bản Heuristic dùng hàm đánh giá trong `heuristic_eval.py`; mỗi bên có một bộ nhớ ô đã đứng riêng để tránh đi lòng vòng.
