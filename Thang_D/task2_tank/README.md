# Task 2 - Tank Battle: Minimax và Alpha-Beta (phần thuật toán)

Dùng engine của team (`engine/`, `maps/`, `tests/test_engine.py`, `tools/` giữ nguyên, không sửa).
Phần thuật toán nằm ở `algorithms/` và `experiments/`. Chỉ dùng thư viện chuẩn của Python 3.8 trở lên.

## Cấu trúc

```
task2_tank/
  engine/        engine của team (GameState, GameMap, Tank, Base, Bullet, Action, Direction)
  maps/          small.txt, medium.txt, full.txt
  algorithms/
    adversarial.py   MinimaxSearch, AlphaBetaSearch, SearchStats, SearchResult
    agents.py        Agent, MinimaxAgent, AlphaBetaAgent, play_match
    scenarios.py     tạo trạng thái xuất phát cho thí nghiệm và test
  experiments/compare_search.py   bảng so sánh Minimax và Alpha-Beta, xuất csv
  tests/test_engine.py            test của team
  tests/test_search.py            test của thuật toán
  play_demo.py                    chạy một ván trong console
```

## Cách chạy (cd vào thư mục Thang_D)

```
python -m unittest discover -s task2_tank/tests -t .
python -m task2_tank.experiments.compare_search
python -m task2_tank.experiments.compare_search --max-horizon 6 --minimax-max-horizon 3 --csv results.csv
python -m task2_tank.play_demo --map small --horizon 3 --ordering --tank-hp 1 --base-hp 1
```

## Giao diện với engine

Thuật toán chỉ gọi `state.player()`, `state.legal_actions()`, `state.result(action)`,
`state.is_terminal()`, `state.utility()` và đọc `state.cycle`, `state.pending`, `state.tanks`, `state.bases`
(chỉ để sắp xếp nước đi). `result()` của engine clone state nên thuật toán không làm thay đổi state gốc.

Agent: `choose_action(state)` trả về `Action`. Đổi tên/chữ ký nếu GUI của nhóm yêu cầu khác.

## Ghi chú

- `horizon` là số cycle nhìn trước. `MAX_CYCLES = 100` của engine là hằng số toàn cục và quá sâu cho Minimax
  thuần, nên thuật toán tự coi trạng thái ở cycle gốc + horizon là kết thúc (utility 0, hòa) mà không sửa engine.
  Đây vẫn là Minimax thuần trên một game ngắn hơn, chưa phải Heuristic Minimax.
- Alpha-Beta cho đúng giá trị gốc như Minimax (có test). Giá trị các nhánh bị cắt trong `action_values` chỉ là cận.
- `move_ordering=True` đưa FIRE lên đầu khi tank đang đối mặt tank hoặc base địch. Khi nhiều hành động cùng giá
  trị, thứ tự duyệt quyết định hành động được chọn nên hành động có thể khác, giá trị thì không.
- Với HP chuẩn (6/9/3) cần ít nhất 6 cycle mới phá được tank, nên horizon nhỏ luôn ra giá trị 0. Thí nghiệm có
  thêm kịch bản HP thấp (chỉnh bằng `set_hp`, không đụng engine).
- MIN chọn sau và biết hành động của MAX nên kết quả Minimax là phương án thận trọng cho MAX (ghi vào báo cáo).
