# Task 3 - Kakuro như một bài toán CSP

Bộ giải Kakuro gồm: lọc miền theo từng run (constraint propagation), Backtracking Search
với các heuristic MRV, Degree, LCV, và giao diện PyGame phát lại quá trình tìm kiếm.

## 1. Cấu trúc thư mục

```
task3_kakuro/
├── __init__.py
├── __main__.py            # dòng lệnh: solve / traces / bench
├── puzzle.py              # Puzzle: đọc JSON, dựng run, peers, check(); dùng chung cho solver và UI
├── requirements.txt       # pygame
├── model/
│   ├── kakuro_model.py    # mô hình CSP: build_runs, check_model, verify, bảng mẫu 5x5 và 9x9
│   └── propagation.py     # Run, Propagator: bảng tổ hợp, node consistency, forward checking, undo
├── solver/
│   ├── heuristics.py      # MRV, Degree (chọn biến), LCV (sắp xếp giá trị)
│   ├── backtracking.py    # BacktrackingSolver, SearchStats, SolveResult
│   └── trace.py           # TraceRecorder: ghi sự kiện theo schema chung cho UI
├── puzzles/
│   ├── assignment_5x5.json
│   └── assignment_9x9.json
├── traces/                # trace sinh sẵn, UI đọc từ đây
│   ├── assignment_5x5.json
│   ├── assignment_9x9.json
│   └── backtrack_demo.json
└── ui/
    ├── app.py             # giao diện PyGame
    └── player.py          # TracePlayer: kiểm tra schema và phát lại sự kiện
```

Luồng dữ liệu: `puzzles/*.json` -> `Puzzle` -> `BacktrackingSolver` (dùng `Propagator`)
-> `TraceRecorder` -> `traces/*.json` -> `TracePlayer` -> giao diện. UI chỉ phát lại
snapshot, không chạy solver.

## 2. Cách chạy

Yêu cầu Python 3.10 trở lên. Các lệnh dưới đây chạy từ **thư mục cha** của `task3_kakuro/`
vì code dùng import tương đối.

```bash
pip install -r task3_kakuro/requirements.txt     # chỉ UI cần pygame

# Giải một puzzle (mặc định MRV+Degree và LCV), in nghiệm và thống kê
python -m task3_kakuro solve task3_kakuro/puzzles/assignment_9x9.json

# Chọn heuristic, giới hạn số nút, xuất trace để xem trong UI
python -m task3_kakuro solve task3_kakuro/puzzles/assignment_9x9.json \
    --variable mrv --value asc --max-nodes 10000 --trace task3_kakuro/traces/my_run.json

# Sinh lại 3 trace mặc định trong traces/
python -m task3_kakuro traces

# So sánh các tổ hợp heuristic trên mọi puzzle trong puzzles/
python -m task3_kakuro bench --repeat 20

# Mở giao diện (mặc định đọc traces/assignment_9x9.json)
python -m task3_kakuro.ui.app
python -m task3_kakuro.ui.app --trace task3_kakuro/traces/backtrack_demo.json

# Kiểm tra riêng tầng model (bảng 5x5 và 9x9 trong kakuro_model.py)
python -m task3_kakuro.model.kakuro_model
```

Lựa chọn của `--variable`: `first` (baseline), `mrv`, `mrv-degree`.
Lựa chọn của `--value`: `asc` (tăng dần), `lcv`.

Phím tắt trong UI: Space phát/dừng, mũi tên trái/phải lùi/tiến một sự kiện, `R` về đầu,
`1`/`2`/`3` chọn trace, `+`/`-` đổi tốc độ, click ô trắng để xem miền và các run chứa ô đó.
Chế độ không cửa sổ: `python -m task3_kakuro.ui.app --headless --screenshot out.png --event 40`.

## 3. Mô hình CSP

- **Biến**: mỗi ô trắng `(r, c)`. 5x5 có 12 biến, 9x9 có 48 biến.
- **Miền**: ban đầu `{1..9}`.
- **Ràng buộc**: mỗi run (dãy ô trắng liên tiếp theo hàng hoặc cột) có hai ràng buộc,
  Alldiff (các ô khác nhau đôi một) và Sum (tổng bằng số gợi ý). Mỗi ô thuộc đúng 2 run.
  Đây là ràng buộc bậc cao nên không dùng AC-3 nguyên bản, xem `t3_propagation.docx`.

## 4. Thuật toán

**Lọc miền (`model/propagation.py`)**
- Bảng `COMBOS[(k, S)]` liệt kê các tập k chữ số khác nhau có tổng S.
- Node consistency: lọc từng run một lần trước khi tìm kiếm (`propagate_all`).
- Forward checking: khi gán `cell = v`, `assign` thu miền ô về `{v}` rồi lọc lại hai run
  chứa ô, lặp tới điểm cố định. Hàm trả về `(ok, removed)` với `removed` là danh sách
  `(ô, giá trị, run gây ra)`; `Propagator.undo` dùng danh sách này để hoàn tác khi quay lui.

**Backtracking (`solver/backtracking.py`)**
1. `propagate_all`, nếu thất bại thì puzzle vô nghiệm.
2. Chọn ô chưa xác định (miền từ 2 giá trị trở lên) bằng `VariableSelector`.
3. Sắp xếp giá trị bằng `ValueOrderer`.
4. Với mỗi giá trị: `assign`; thành công thì đệ quy, thất bại thì `undo` và thử giá trị kế.
5. Hết ô chưa xác định thì đã có nghiệm; `Puzzle.check` xác minh lại độc lập.

**Heuristic (`solver/heuristics.py`)**

| Lớp | Vai trò | Quy tắc |
|---|---|---|
| `FirstUnassigned` | baseline | ô chưa gán đầu tiên theo hàng, cột |
| `MRV` | chọn biến | miền nhỏ nhất |
| `MRVDegree` | chọn biến | MRV, hòa thì ô có nhiều ô chưa gán cùng run nhất (Degree) |
| `AscendingOrder` | chọn giá trị | tăng dần |
| `LCV` | chọn giá trị | thử gán từng giá trị bằng `assign`, đếm số giá trị bị loại ở các ô khác rồi hoàn tác; ít nhất thử trước, giá trị dẫn tới mâu thuẫn xếp cuối |

Mọi hòa đều được phá theo thứ tự `(hàng, cột)` hoặc giá trị nhỏ trước nên kết quả tái lập được.
Thêm heuristic mới bằng cách kế thừa `VariableSelector` hoặc `ValueOrderer` và đăng ký
vào `VARIABLE_SELECTORS` / `VALUE_ORDERERS`.

## 5. Kết quả thử nghiệm

Kết quả từ `python -m task3_kakuro bench` (mọi nghiệm đều qua `Puzzle.check`;
thời gian thay đổi theo máy, số nút và số lần quay lui thì cố định):

| Puzzle | Biến | Giá trị | Nút | Quay lui | Độ sâu tối đa |
|---|---|---|---:|---:|---:|
| 9x9 | first | asc | 9 | 2 | 7 |
| 9x9 | first | lcv | 48 | 41 | 7 |
| 9x9 | mrv | asc | 28 | 17 | 11 |
| 9x9 | mrv | lcv | 48 | 37 | 11 |
| 9x9 | mrv-degree | asc | 12 | 3 | 9 |
| 9x9 | mrv-degree | lcv | 18 | 9 | 9 |

Nhận xét: Degree giảm rõ số nút so với MRV thuần (28 xuống 12 với `asc`). Trên puzzle 9x9
này LCV không giúp giảm số nút: puzzle có nghiệm duy nhất, và "ít loại giá trị nhất"
không đồng nghĩa với "đúng", nên LCV tốn thêm chi phí thử gán mà không tránh được nhánh sai.
`first + asc` ít nút nhất (9) chủ yếu do thứ tự quét hàng-cột hợp với puzzle này, không
nên coi là tổng quát. Cần thêm puzzle để kết luận chắc hơn.

## 6. Định dạng trace (schema_version 1)

```json
{
  "schema_version": 1,
  "puzzle": { "name": "...", "grid": [["#", "d21", "."]] },
  "meta": { "variable": "mrv-degree", "value": "lcv", "max_nodes": null },
  "events": [ { "kind": "...", "cell": "r,c" | null, "message": "...", "removed": [..],
                "nodes": 0, "backtracks": 0, "depth": 0,
                "domains": { "r,c": [1, 2] } } ]
}
```

| kind | Khi nào phát | Trường thêm |
|---|---|---|
| `start` | miền ban đầu 1..9 | |
| `propagate` | một run loại giá trị khỏi miền một ô (cả ở node consistency và sau mỗi phép gán) | `run` |
| `assign` | phép đoán `cell = value`, message ghi lý do chọn (MRV, Degree, LCV) | `value` |
| `contradiction` | miền rỗng hoặc run không còn tổ hợp hợp lệ | `run` |
| `backtrack` | hoàn tác phép gán, miền được khôi phục | `value`, `restored` |
| `solution` | tìm thấy nghiệm | |
| `exhausted` | duyệt hết mà không có nghiệm | |
| `limit` | dừng vì chạm `--max-nodes` | |

Mỗi sự kiện chứa miền của **tất cả** ô trắng tại thời điểm đó, nên `TracePlayer` phát lại
được mà không cần biết solver cài đặt thế nào. Ý nghĩa màu trong UI: xanh dương là đoán,
xanh ngọc là lan truyền, cam là hoàn tác, đỏ gạch ngang là giá trị vừa bị loại.
