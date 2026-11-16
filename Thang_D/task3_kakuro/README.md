# Task 3 - Kakuro (CSP): kịch bản chạy demo

Kịch bản này vừa là hướng dẫn cài đặt, vừa là thứ tự các bước để quay demo và trả lời phỏng vấn.
Toàn bộ lệnh chạy từ **thư mục cha** của `task3_kakuro/` (code dùng import tương đối).
Yêu cầu: Python 3.10 trở lên. Chỉ giao diện cần pygame.

## 0. Chuẩn bị (1 phút)

```bash
pip install -r task3_kakuro/requirements.txt
python -m task3_kakuro test                  # 50 test, kỳ vọng: OK
```

Nếu báo `No module named task3_kakuro` hoặc `attempted relative import`: bạn đang đứng trong
thư mục `task3_kakuro`; hãy `cd ..` rồi chạy lại. Nếu báo `Could not open requirements file`: cũng do
đứng sai thư mục.

Hai bảng trong đề đã có sẵn ở `puzzles/` (chép tay từ PDF, mỗi bảng có đúng 1 nghiệm):

| File | Bảng trong đề | Biến | Run |
|---|---|---:|---:|
| `assignment_5x5.json` | ví dụ ở trang 4 | 12 | 8 |
| `assignment_9x9.json` | bảng phức tạp ở trang 5 | 48 | 28 |

Thêm bảng mới: bỏ một file `.json` vào `puzzles/`, CLI và UI tự nhận. Định dạng ô: `.` ô trắng,
`#` ô đen, `d21` tổng cột bên dưới, `a12` tổng hàng bên phải, `d14/a12` cả hai.

---

## Cảnh 1 - Mô hình hóa CSP (Requirement 1)  ~2 phút

**Nói:**
- **Biến**: mỗi ô trắng `(r, c)`. Bảng 5x5 có 12 biến, 9x9 có 48 biến.
- **Miền**: ban đầu `{1..9}`.
- **Ràng buộc**: mỗi *run* (dãy ô trắng liền nhau theo hàng hoặc cột, bắt đầu từ một ô gợi ý)
  có hai ràng buộc: **Alldiff** (các ô khác nhau đôi một) và **Sum** (tổng bằng số gợi ý).
  Mỗi ô trắng thuộc đúng 2 run (một ngang, một dọc).
- Đây là ràng buộc bậc cao (nhiều biến), nên không dùng AC-3 nhị phân nguyên bản. Thay vào đó mỗi
  run lọc miền bằng **bảng tổ hợp**: `(k ô, tổng S)` -> các tập k chữ số khác nhau có tổng S.

**Chỉ code:** `model/cell.py` (`Cell`), `model/domains.py` (`Domains`), `model/constraint.py`
(`Run`, `CombinationTable`), `model/board.py` (`KakuroBoard` dựng các `Run` từ bảng).

**Ví dụ minh họa (bảng 5x5):** run ngang `A1` gồm 2 ô, tổng 12 -> chỉ có các tập `{3,9} {4,8} {5,7}`
(không có 6+6 vì Alldiff), nên các chữ số 1, 2 và 6 bị loại khỏi hai ô đó ngay từ đầu.

---

## Cảnh 2 - Giải bằng dòng lệnh (Requirement 2)  ~3 phút

```bash
python -m task3_kakuro solve task3_kakuro/puzzles/assignment_5x5.json
python -m task3_kakuro solve task3_kakuro/puzzles/assignment_9x9.json
```

**Kỳ vọng:** cả hai in `solved, verified=True`. Với 9x9 (mặc định `mrv-degree` + `lcv`):
`nodes=18  backtracks=9  max_depth=9`, nghiệm:

```
# # # # # # # # #
# # 5 9 8 # 1 2 #
# # 2 7 1 3 4 6 5
# 8 6 # # 1 2 8 9
# 9 8 # 3 2 8 9 #
# # 9 8 6 5 # 7 5
# 3 4 5 2 # # 4 2
# 9 3 7 1 6 8 5 #
# # 7 9 # 1 4 3 #
```

`verified=True` nghĩa là nghiệm đã được `Puzzle.check` kiểm tra độc lập (mọi run đúng tổng và các
chữ số khác nhau), không chỉ dựa vào solver.

**Nói về thuật toán (`solver/backtracking.py`):**
1. Lan truyền ràng buộc ban đầu: mọi run được lọc, và khi miền một ô đổi thì các run còn lại chứa ô
   đó được xếp lại hàng đợi, lặp tới điểm cố định (`model/propagation.py`).
2. Chọn biến chưa xác định bằng **MRV** (miền nhỏ nhất), hòa thì **Degree** (nhiều ô chưa gán cùng run nhất).
3. Sắp xếp giá trị bằng **LCV** (thử gán, đếm số giá trị bị loại ở ô khác, ít nhất thử trước).
4. Gán `cell = v`, lan truyền lại hai run chứa ô đó. Thất bại thì hoàn tác (`Domains.restore`) và thử giá trị kế.
5. Hết ô chưa xác định là đã có nghiệm.

---

## Cảnh 3 - So sánh heuristic, độ đúng và độ ổn định (Requirement 2)  ~3 phút

```bash
python -m task3_kakuro bench --repeat 20
```

Bảng so sánh 3 cách chọn biến x 2 cách chọn giá trị trên cả hai bảng; thời gian là trung vị của
20 lần chạy (thời gian phụ thuộc máy, số nút và số lần quay lui thì cố định):

| Bảng | Biến | Giá trị | Nút | Quay lui | Độ sâu tối đa |
|---|---|---|---:|---:|---:|
| 5x5 | mọi tổ hợp | | 1 đến 4 | 0 đến 3 | 1 |
| 9x9 | first | asc | 9 | 2 | 7 |
| 9x9 | first | lcv | 48 | 41 | 7 |
| 9x9 | mrv | asc | 28 | 17 | 11 |
| 9x9 | mrv | lcv | 48 | 37 | 11 |
| 9x9 | mrv-degree | asc | 12 | 3 | 9 |
| 9x9 | mrv-degree | lcv | 18 | 9 | 9 |

**Điểm để nói:**
- Cả 6 tổ hợp đều ra **cùng một nghiệm** và đều qua `Puzzle.check`: solver đúng.
- Kết quả **tái lập được**: mọi trường hợp hòa đều phá theo thứ tự `(hàng, cột)` hoặc giá trị nhỏ trước,
  nên số nút và số lần quay lui không đổi giữa các lần chạy.
- Degree giảm rõ so với MRV thuần (28 -> 12 nút với `asc`).
- LCV **không** giúp ở bảng này: nghiệm duy nhất, "ít loại giá trị nhất" không đồng nghĩa với "đúng",
  nên LCV chỉ tốn thêm chi phí thử gán. `first + asc` ít nút nhất (9) chủ yếu do thứ tự quét hàng-cột
  hợp với bảng này, không nên coi là tổng quát. Chỉ có một bảng phức tạp nên chưa kết luận chắc hơn.

Kiểm thử tự động (đã chạy ở Cảnh 0) bao phủ: nghiệm là duy nhất (đếm bằng tìm kiếm độc lập),
lan truyền không bao giờ loại mất nghiệm đúng, `assign` rồi `undo` khôi phục miền chính xác,
giới hạn nút (`--max-nodes`), và bảng lỗi được báo `unsolvable`.

---

## Cảnh 4 - Giao diện trực quan (Requirement 3)  ~6 phút

```bash
python -m task3_kakuro.ui.app
```

Mở bảng 9x9 với `mrv-degree + lcv`. Solver chạy **trong thread riêng song song với UI** và chỉ sinh
thêm một sự kiện khi người xem đi tới sự kiện cuối (hoặc bấm Finish); thuật toán không có đoạn code riêng cho UI.

Chuỗi thao tác gợi ý (số sự kiện lấy từ cấu hình mặc định trên 9x9, tổng cộng 303 sự kiện):

| Bước | Thao tác | Chỉ ra gì |
|---|---|---|
| 1 | Nhìn bàn cờ ở sự kiện `001 START` | Mọi ô trắng hiện đủ 9 chữ số nhỏ 1..9: đây là **miền** ban đầu. |
| 2 | Bấm **Next** hoặc **Play** vài lần (sự kiện 2 đến 97) | Màu xanh ngọc `PROPAGATE`: cả run được tô nhạt, giá trị bị loại hiện **gạch đỏ**; dòng `A3 (sum 28) removes [8, 9]...` nêu run nào gây ra. |
| 3 | Bấm vào một ô trắng | **CELL INSPECTOR** hiện miền của ô và, với mỗi run chứa ô, các tập chữ số còn hợp lệ (`sets:`): đó chính là thứ quyết định giá trị nào bị loại. |
| 4 | Bấm **Next guess** (hoặc phím `G`) | Tới sự kiện 98, `ASSIGN`: ô viền xanh, chữ số xanh dương là **phép đoán**; thông báo ghi lý do chọn (`MRV |D|=..., Degree=...; LCV cost=...`); **GUESS STACK** có thêm một phần tử. |
| 5 | Bấm Next sau phép đoán | Chuỗi `PROPAGATE` sau phép đoán: chữ số xanh ngọc là giá trị **suy ra** do lan truyền. |
| 6 | Bấm **Next backtrack** (phím `B`) | Tới sự kiện 166 `BACKTRACK` (ngay trước đó 165 là `CONTRADICTION`, màu đỏ: một miền rỗng hoặc run hết tổ hợp). Miền được khôi phục, GUESS STACK ghi `undone (r,c)=v`. |
| 7 | Kéo **thanh tiến độ** dưới bàn cờ | Mỗi cột là loại sự kiện nổi bật nhất (xanh dương = đoán, cam = quay lui, đỏ = mâu thuẫn, xanh lá = nghiệm). Nhảy lùi/tiến tới bất kỳ đâu không làm solver chạy thêm. |
| 8 | Bấm **Finish** rồi xem sự kiện cuối | Khung **RESULT**: `SOLVED, verified by Puzzle.check`, số nút, số lần quay lui, độ sâu tối đa, thời gian giải thuần của solver. |
| 9 | Bấm nút `var:`/`val:` (hoặc phím `V` / `C`) | Đổi heuristic, chạy lại solver trên cùng bảng. Thử `first + asc`: quay lui đầu tiên ở sự kiện 135, tổng 209 sự kiện; `mrv + asc`: sự kiện 110, tổng 333. |
| 10 | Bấm nút `1` / `2` hoặc Tab | Chuyển giữa bảng 5x5 (41 sự kiện, **không quay lui**) và 9x9. |

### Bảng điều khiển

| Thao tác | Tác dụng |
|---|---|
| Space, nút Play/Pause | phát / dừng |
| Mũi tên trái / phải | lùi / tiến một sự kiện |
| `G`, nút **Next guess** | nhảy tới phép đoán kế tiếp (bỏ qua chuỗi lan truyền) |
| `B`, nút **Next backtrack** | nhảy tới lần quay lui kế tiếp |
| Bấm / kéo **thanh tiến độ** | nhảy tới vị trí bất kỳ trong các sự kiện đã sinh |
| `R` | về đầu |
| `1`..`9`, Tab | chọn puzzle |
| `F`, nút Finish | cho solver chạy hết |
| `V` / `C` | đổi heuristic chọn biến / chọn giá trị |
| `+` / `-` | đổi tốc độ phát |
| Bấm một ô trắng | xem miền và các run chứa ô đó |

### Cách đọc màu

- **Ô viền xanh + chữ xanh dương**: phép đoán. **Chữ xanh ngọc**: giá trị suy ra do lan truyền.
  **Chữ nhỏ 1..9**: miền còn lại. **Chữ gạch đỏ**: giá trị vừa bị loại.
- **Cả run tô nhạt**: sự kiện `propagate` (xanh ngọc) hoặc `contradiction` (đỏ).
- Sự kiện: `start`, `propagate`, `assign`, `contradiction`, `backtrack`, `solution`, `exhausted`, `limit`.

Chụp ảnh không cửa sổ (dùng cho báo cáo): 

```bash
python -m task3_kakuro.ui.app --headless --screenshot out.png --event 40
```

Tham số khác: `--puzzle <file.json>`, `--variable first|mrv|mrv-degree`, `--value asc|lcv`.

---

## Cảnh 5 - Kiến trúc OOP (nếu được hỏi)  ~1 phút

```
task3_kakuro/
├── __main__.py, cli.py     # KakuroCli: solve / bench / test
├── puzzle.py               # Puzzle (bài toán CSP của một bảng), PuzzleRepository (kho puzzles/*.json)
├── model/                  # Cell, Domains, Constraint/Run/CombinationTable, KakuroBoard, Propagator
├── solver/                 # VariableSelector, ValueOrderer (MRV, Degree, LCV), BacktrackingSolver,
│                           # SolverFactory, TraceRecorder/TraceEvent, LiveSession (thread solver)
├── ui/                     # KakuroApp, AppLauncher, InputController, Canvas, Theme,
│                           # 5 View (chỉ vẽ), LivePlayer (vị trí đang xem, seek, tổng kết)
├── puzzles/                # assignment_5x5.json, assignment_9x9.json
└── tests/                  # unittest, chạy bằng `python -m task3_kakuro test`
```

Điểm thiết kế: heuristic là các lớp con của `VariableSelector` / `ValueOrderer` (Strategy), thêm heuristic
mới chỉ cần kế thừa rồi đăng ký vào `VARIABLE_SELECTORS` / `VALUE_ORDERERS` trong `solver/heuristics.py`;
solver không biết UI tồn tại, UI chỉ đọc danh sách `TraceEvent` mà `LiveSession` sinh ra.

Luồng dữ liệu: `puzzles/*.json` -> `PuzzleRepository` -> `Puzzle` (`KakuroBoard` dựng các `Run`) ->
`BacktrackingSolver` (dùng `Propagator`) chạy trong thread của `LiveSession` -> `TraceRecorder` đẩy sự kiện
-> `LivePlayer` -> các View.

---

## Phụ lục - Lệnh dòng lệnh khác

```bash
python -m task3_kakuro solve --all                                   # giải mọi puzzle trong puzzles/
python -m task3_kakuro solve <file.json> --variable mrv --value asc --max-nodes 10000
python -m task3_kakuro solve <file.json>                             # bảng không hợp lệ: in [canh bao], unsolvable, mã thoát 1
```

`--variable`: `first` (baseline), `mrv`, `mrv-degree`. `--value`: `asc` (tăng dần), `lcv`.
Bảng không hợp lệ (ví dụ run có tổng không thể đạt) vẫn được nạp kèm `Puzzle.warnings`; solver kết luận
`unsolvable` ngay ở bước lan truyền ban đầu (0 nút), UI hiện dòng `WARNING` và nút puzzle có dấu `!`.
