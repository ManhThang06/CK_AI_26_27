# Task 2 — Kịch bản demo Tank Battle

## Chuẩn bị trước buổi demo

Giải nén để có thư mục `task2_tank`. Mở terminal tại thư mục cha chứa `task2_tank`.
Dùng Python 3.8 trở lên và cài Pygame.

```bash
python -m pip install -r task2_tank/requirement.txt
python -m unittest discover -s task2_tank/tests -t .
python task2_tank/run_gui.py
```

Trên macOS, nếu máy dùng tên lệnh `python3`, thay `python` bằng `python3` trong các lệnh.
Tệp requirement.txt ghi thư viện GUI. Phần tìm kiếm, engine và thí nghiệm chỉ dùng thư viện chuẩn.
Bản đóng gói đã kiểm tra trên Windows với Python 3.12 và Pygame 2.6.1. Cần chạy lại trên macOS 13.7.8 Intel i5 theo cấu hình chấm của đề.

## Cảnh 1 — Giới thiệu bài toán và OOP, khoảng 1 phút

Mở menu, giới thiệu ba bản đồ small, medium và full.

Lời trình bày gợi ý

> Nhóm mô hình Tank Battle thành trò chơi hai người tổng bằng không. P1 là MAX, P2 là MIN.
> Trạng thái gồm kích thước map, tường và HP, vị trí và hướng hai tank, HP tank/base, đạn,
> số cycle và hành động đang chờ của MAX. MAX chọn trước, MIN nhìn thấy lựa chọn này,
> rồi engine giải quyết một cycle. Mỗi cycle tương ứng hai ply trong cây tìm kiếm.
> Utility được tính từ phía MAX, thắng +1, thua -1, hòa 0. Lợi ích của MIN mang dấu ngược lại.

Mở các file để chỉ trách nhiệm của đối tượng.

| Thành phần | Lớp và trách nhiệm |
|---|---|
| `engine/game_state.py` | `GameState` cung cấp player, legal_actions, result, is_terminal, utility |
| `engine/entities.py` | `Tank`, `Base`, `Bullet` lưu dữ liệu thực thể và sao chép |
| `engine/game_map.py` | `GameMap` đọc bản đồ |
| `algorithms/adversarial.py` | `AdversarialSearch` là lớp cha, hai lớp con triển khai Minimax và Alpha–Beta |
| `algorithms/heuristic_search.py` | Hai lớp heuristic dùng chung phần duyệt cây, khác cờ cắt tỉa |
| `algorithms/agents.py` | `Agent` là lớp trừu tượng, các agent cùng có choose_action(state) |
| `engine/match.py` | `SafeAgent` xử lý lỗi/đo thời gian, `MatchSession` điều phối trận |
| `gui/game_controller.py` | `GameController` kế thừa MatchSession, bổ sung log và sự kiện để vẽ |
| `gui/app.py`, `gui/renderer.py` | Menu, vòng lặp Pygame và hiển thị |

Các hàm hình học, CLI và hàm tạo kịch bản được giữ ở dạng hàm khi chúng không cần quản lý trạng thái riêng.
DSA được dùng gồm cây tìm kiếm đệ quy, dictionary, deque, Counter, heap và Dijkstra tính đường tiến công.

## Cảnh 2 — Chứng minh luật game, khoảng 1–2 phút

Chọn map small, hai bên Human, bắt đầu ván.

| Nội dung kiểm tra | Thao tác và kết quả cần thấy |
|---|---|
| Di chuyển | Tank đi một ô bằng phím điều khiển |
| Sáu hành động | Bốn hướng, FIRE và STAY |
| HP | Tank 6, base 9, tường 3; mỗi hit trừ 1 |
| Đạn | FIRE theo hướng nòng, mỗi cycle tối đa 3 ô |
| Va chạm | Đạn kiểm tra sau từng ô, dừng ngay khi trúng vật đầu tiên |
| Kết thúc | Tank hoặc base bị phá thì dừng trận, hiển thị kết quả |

Điều khiển P1 bằng W/A/S/D, Space bắn, Q đứng yên.
Điều khiển P2 bằng phím mũi tên, Enter bắn, Right Shift đứng yên.
P tạm dừng, N chạy từng cycle cho các lượt AI, +/- đổi tốc độ, R khởi động lại, Esc về menu.
Các phím hành động của người chơi vẫn thực hiện lượt khi đang pause để có thể demo từng nước.

Chỉ vào `_resolve_cycle()` và `_advance_bullets()` để giải thích kiểm tra va chạm từng ô.
Tank bị phá bởi đạn cũ trước giai đoạn bắn không được sinh đạn mới.
Các viên đạn trong cùng một bước con được xử lý, sau đó kiểm tra kết thúc trước bước con tiếp theo.

Các quy ước bổ sung cần trình bày rõ với giảng viên

- Hòa sau 100 cycle nếu hai bên vẫn hoạt động. Đây là giới hạn trận của nhóm.
- Mỗi tank có tối đa một viên đạn đang bay. FIRE khi đã có đạn được xử lý như đứng yên.
- Hai tank cùng đến một ô trống thì ưu tiên luân phiên theo cycle. Đổi chỗ trực tiếp bị chặn.
- Hai bên cùng bị phá trong cùng bước xử lý đạn được tính hòa.
- MIN quan sát hành động pending của MAX. Mô hình này là thông tin hoàn hảo theo lượt.

## Cảnh 3 — Giải thích bốn cấu hình tìm kiếm, khoảng 2 phút

| Cấu hình | Hàm đánh giá lá và cách duyệt |
|---|---|
| Minimax | MAX lấy lớn nhất, MIN lấy nhỏ nhất; duyệt đầy đủ trong phạm vi đặt ra |
| Alpha–Beta | Cùng phép đánh giá với Minimax, cắt khi MAX đạt beta hoặc MIN đạt alpha |
| Heuristic Minimax | Cắt ở độ sâu giới hạn, dùng Eval ở trạng thái chưa kết thúc |
| Heuristic Alpha–Beta | Cùng Eval và cutoff, thêm cắt tỉa Alpha–Beta |

Lời trình bày gợi ý

> Khi không truyền horizon, Minimax và Alpha–Beta đi đến terminal thật của engine.
> Cây từ đầu trận quá lớn, nên GUI và bảng thí nghiệm dùng horizon theo số cycle.
> Với horizon_score bật, hai cấu hình đầu dùng chênh lệch tổng HP chia 100 ở cutoff.
> Đây là Minimax/Alpha–Beta giới hạn độ sâu với đánh giá HP đơn giản.
> Hai cấu hình heuristic dùng Eval đầy đủ. Em phân biệt terminal thật với cutoff trong thống kê.
> Test gần cuối trận xác nhận hai thuật toán không đặt horizon cho cùng utility và không có cutoff.

Không tuyên bố đã duyệt toàn bộ cây từ đầu trận. Cutoff đánh giá HP cũng là một hàm ước lượng.
Trong phạm vi cây và hàm lá giống nhau, cắt tỉa Alpha–Beta bảo toàn giá trị gốc.

Mở `HeuristicEvaluator.evaluate()` để trình bày các đặc trưng.
Eval ưu tiên HP base/tank, khả năng tiến công base địch, hướng bắn, đạn, độ linh hoạt và lịch sử lặp.
Dijkstra ước lượng đường tới vị trí có thể bắn base địch. Trọng số phá tường là 1 + HP của tường.
Chi phí này là đặc trưng chiến thuật, chưa mô phỏng đủ thời gian đạn bay và giới hạn đạn.
Điểm kết thúc thật được đặt lớn hơn điểm ước lượng thông thường, có ưu tiên thắng sớm/thua muộn.

## Cảnh 4 — Demo các lỗi đã xử lý, khoảng 2 phút

### Minimax và Alpha–Beta giảm chạy vòng

Chọn map medium hoặc full, P1 Minimax, P2 Alpha–Beta, depth 2.

> Ở horizon nông, nhiều hành động có cùng điểm HP. Chọn ngẫu nhiên đơn thuần dễ tạo đường đi vòng.
> Agent giờ ghi nhớ vị trí gần đây và trạng thái lặp. Khi nhiều hành động cùng điểm ở gốc,
> agent dùng đánh giá chiến thuật một cycle để phá hòa và hạn chế quay lại đường cũ.
> Điểm minimax là tiêu chí chính. Phá hòa là phần điều khiển bổ sung khi chơi GUI.

Theo dõi tank tiến công và thay đổi hướng bắn, kiểm tra HP đối thủ/tường thay vì chỉ đếm số hướng di chuyển.
Giảm lặp là heuristic thực dụng, chưa bảo đảm mọi tình huống đều thoát được giằng co.

### Heuristic Minimax depth 3–4 phản hồi theo ngân sách

Chọn Heuristic Minimax, lần lượt depth 3 và 4.

> Agent dùng iterative deepening từ độ sâu 1, tăng dần đến mức chọn trong menu.
> Ngân sách suy nghĩ GUI là 0,5 giây mỗi quyết định. Nếu chưa duyệt xong mức tiếp theo,
> agent dùng kết quả của mức đã hoàn tất. HUD hiển thị d là độ sâu thực sự hoàn tất.
> Vì thế chọn depth 4 có thể chỉ hoàn tất depth 2 hoặc 3 trên máy đang chạy.

Thời gian có thể vượt nhẹ ngân sách vì việc kiểm tra diễn ra trong vòng tìm kiếm và một số phép đánh giá.
Nếu chưa hoàn tất depth 1 trước hạn, hành động dự phòng là STAY.
Pygame tiếp tục nhận sự kiện trong khi AI chạy trên thread nền.
Restart hoặc trở về menu tạo hàng đợi kết quả riêng để thread của ván cũ không ghi đè kết quả ván mới.

## Cảnh 5 — Thí nghiệm so sánh, khoảng 1–2 phút

Chạy kiểm tra nhanh trước mặt giảng viên.

```bash
python -m task2_tank.experiments.compare_search --max-depth 2 --repeats 2
```

Chạy đủ bảng độ sâu 1–3 khi chuẩn bị báo cáo.

```bash
python -m task2_tank.experiments.compare_search --max-depth 3 --repeats 2
```

> Bốn cấu hình dùng cùng 12 kịch bản, gồm ba map với bốn trạng thái đầu/giữa ván.
> Cùng độ sâu, tắt ordering và lọc nước, đánh giá tất định. Mỗi lần đo xóa cache đường đi
> để cấu hình chạy sau không hưởng cache của cấu hình trước.
> Bảng lưu thời gian nhỏ nhất qua số lần lặp và lấy trung bình trên các kịch bản.
> Đây là phép đo ở độ sâu cố định, khác chế độ GUI có ngân sách thời gian.

Mở `experiments/results/compare_search_raw.csv` và `compare_search_summary.csv`.
Giải thích các cột nodes_generated, nodes_expanded, terminal_nodes, cutoff_nodes, heuristic_evals,
cutoffs, pruned_branches, root_value và max_depth_ply.
Một cycle có hai ply. Số nút con tạo ra tăng nhanh khi tăng độ sâu.
Kiểm tra cuối chương trình phải báo Minimax và Alpha–Beta cùng giá trị gốc trong từng cặp.
`environment.json` lưu cấu hình máy và số lần lặp để tái lập.

Giải đấu được chạy bằng lệnh sau. Các agent đấu trên ba map và đổi bên.

```bash
python -m task2_tank.experiments.tournament --depth 2
```

Giải đấu dùng độ sâu cố định, có phá hòa và lịch sử như cấu hình chơi.
Plugin ngẫu nhiên mẫu dùng seed 42. Phá hòa của hai agent cơ bản có ngẫu nhiên nên kết quả giải đấu có thể thay đổi khi chạy lại. CSV ghi số ván thắng/hòa/thua và thời gian quyết định trung bình.
Thắng nhiều trong tập map thử chưa chứng minh chiến lược tối ưu trên mọi map.

## Cảnh 6 — Nạp thuật toán nhóm khác, khoảng 1 phút

Chỉ file `plugins/example_random_agent.py`, sau đó về menu bấm Reload plugins hoặc F5.
Chọn Random [plugin] cho một bên và một thuật toán của nhóm cho bên còn lại.

Hợp đồng plugin

```python
from task2_tank.engine import Action

class ExternalAgent:
    name = "Agent nhóm khác"

    def choose_action(self, state):
        return Action.STAY


def create_agent():
    return ExternalAgent()
```

> Plugin đặt trong thư mục plugins. Hệ thống nạp create_agent() hoặc lớp có choose_action(state).
> state.player() cho biết bên đang đi. Plugin trả về Action của cùng engine.
> Bộ bọc truyền bản sao trạng thái, đo thời gian, bắt exception và thay hành động sai bằng STAY.

Plugin cần tự kết thúc choose_action. Bộ bọc chưa cưỡng chế dừng plugin có vòng lặp vô hạn.
Chỉ nạp code đã kiểm tra vì import plugin thực thi Python trên máy.

## Cảnh 7 — Kết luận và kiểm tra trước khi nộp

- Yêu cầu 2.1 được minh họa bằng mô hình GameState, MAX/MIN, sáu hành động, transition và utility.
- Yêu cầu 2.2 được minh họa bằng bốn cấu hình, kiểm tra giá trị gốc và CSV cùng điều kiện tìm kiếm.
- Yêu cầu 2.3 được minh họa bằng GUI Pygame, menu chọn agent, plugin và đấu chung engine.
- OOP thể hiện qua lớp trạng thái, lớp tìm kiếm, lớp agent, MatchSession và GameController.
- Test đã tách thành engine, search, heuristic, controller và plugin, bổ sung hồi quy tank chết vẫn bắn.
- Hai log TXT lặp nội dung CSV và các file cache Python được loại khỏi gói.
- play_demo vẫn giữ để tương thích, dùng cùng MatchSession và hỗ trợ cả bốn thuật toán.
- Các vòng đệ quy MAX/MIN của Minimax và Alpha–Beta được giữ rõ ràng để dễ đối chiếu bài giảng.

Demo console độc lập GUI

```bash
python -m task2_tank.play_demo --map small --max-agent heuristic-ab --min-agent random --horizon 2 --seed 42
```

Báo cáo IEEE tối đa 5 trang, video demo và thư mục nộp đúng mẫu là phần đóng gói toàn dự án theo đề.
Gói này chứa riêng Task 2. Số liệu trong results là kết quả chạy thực tế trên máy ghi trong environment.json.

## Kết quả kiểm tra bản đóng gói

- 26 test tự động đạt.
- So sánh đủ 144 dòng kết quả từ 12 kịch bản, ba độ sâu và bốn cấu hình, mỗi cấu hình lặp hai lần.
- Hai cặp Minimax/Alpha–Beta cho cùng giá trị gốc ở toàn bộ 36 điều kiện mỗi cặp.
- Giải đấu chạy đủ 60 ván ở độ sâu cố định 2.
- Kiểm tra GUI với SDL dummy đã render menu, bàn chơi, HUD và reset ván.
- `realtime_check.json` lưu phép đo riêng tám cấu hình GUI ở depth 3 và 4 trên map full.
- Phép đo realtime là kiểm tra mẫu trên máy hiện tại. Ngân sách 0,5 giây là giới hạn mềm.
