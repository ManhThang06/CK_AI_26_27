# Task 1 - N-Queens: Local Search & Propositional Logic

Giải bài toán N-quân hậu theo hai hướng:

| Yêu cầu của đề | Nội dung | Mã nguồn |
|---|---|---|
| Req 1 | Mô hình hóa logic mệnh đề và chuyển sang CNF | `cnf_encoder.py` |
| Req 2 | Giải bằng **Glucose3** (PySAT), đo số clause và thời gian khi N tăng | `sat_solver.py`, `sat_experiment.py` |
| Req 3 | **Min-Conflicts** + heuristic chọn biến, thực nghiệm so sánh | `min_conflicts.py`, `mc_experiment.py` |

## 1. Cấu trúc thư mục

```
Thang_D/                        <- chạy mọi lệnh từ thư mục này
└── task1_nqueens/
    ├── README.md
    ├── requirement.txt        <- thư viện cần cài
    ├── board.py               Board: kiểm tra nghiệm (columns[row] = col), lớp cha của ConflictBoard
    ├── nqueens_solver.py      NQueensSolver (lớp trừu tượng): SATSolver, MinConflictsSolver kế thừa
    ├── variable_selectors.py  VariableSelector: Standard/MaxTabu/RouletteSelector (Strategy)
    ├── experiment_base.py     Experiment (lớp trừu tượng): ghi CSV/môi trường
    ├── cnf_encoder.py         CNFEncoder: sinh các clause CNF
    ├── sat_solver.py          SATSolver: giải bằng Glucose3
    ├── sat_experiment.py      SATExperiment: đo SAT theo N  -> data/measured/sat*.csv
    ├── min_conflicts.py       ConflictBoard (kế thừa Board) + MinConflictsSolver
    ├── mc_experiment.py       MinConflictsExperiment: đo Min-Conflicts -> data/measured/minconf*.csv
    ├── analysis.py            SATPlotter, MinConflictsPlotter, TabuPlotter: vẽ biểu đồ từ CSV
    ├── experiments/
    │   ├── t1_sat.ipynb           notebook Req 2 (đã giữ output)
    │   └── t1_minconflicts.ipynb  notebook Req 3 (đã giữ output)
    └── data/measured/         số liệu đo thật + biểu đồ (figures/)
```

## 2. Cài đặt

Cần Python 3.10 trở lên (đã thử trên Python 3.13).

```bash
cd Thang_D
python -m venv .venv
.venv\Scripts\activate
pip install -r task1_nqueens/requirement.txt
```

> **Quan trọng:** luôn chạy bằng `python -m task1_nqueens.<tên_module>` **từ thư mục `source/`**
> (thư mục chứa `task1_nqueens/`). Chạy trực tiếp `python sat_solver.py` trong thư mục con
> sẽ lỗi vì các module dùng import tương đối.

## 3. Cách chạy

### Req 1 và Req 2 - SAT với Glucose3

Giải một bàn cờ (mặc định N = 8), in số biến, số clause, thời gian và bàn cờ:

```bash
python -m task1_nqueens.sat_solver 8
python -m task1_nqueens.sat_solver 12
```

Thực nghiệm với N tăng dần (N = 4, 5, 8, 12, 16, 24, 32, 48, 64; mỗi N chạy 5 lần):

```bash
python -m task1_nqueens.sat_experiment --repeats 5
# tùy chọn: --ns 4 8 16 32   --output <thư mục>
```

Kết quả: `data/measured/sat.csv` (từng lượt), `sat_summary.csv` (trung bình, độ lệch chuẩn),
`environment.json` (máy đo) và `figures/sat_clauses.png`, `figures/sat_time.png`.

Số clause của mã hóa: với mỗi hàng 1 clause "ít nhất một quân" và với mỗi nhóm k ô (hàng, cột, đường chéo)
có C(k, 2) clause "nhiều nhất một quân" dạng `(¬a ∨ ¬b)`. Ví dụ N = 4 → 80 clause, N = 8 → 736 clause.

### Req 3 - Min-Conflicts

Chạy toàn bộ thực nghiệm (khoảng 10-20 giây): 30 seed × N ∈ {8, 16, 32, 64, 100, 200} × 3 biến thể,
cả **không restart** và **có restart**, cùng thí nghiệm `tabu_size`:

```bash
python -m task1_nqueens.mc_experiment
# tùy chọn: --seeds 10   --ns 8 16 32   --output <thư mục>
```

Kết quả trong `data/measured/`:

| File | Nội dung |
|---|---|
| `minconf.csv` | từng lượt chạy, **không** restart |
| `minconf_restart.csv` | từng lượt chạy, **có** restart (`restart_after = max(50, N)`) |
| `minconf_tabu.csv` | ảnh hưởng của `tabu_size` ∈ {0, 2, 5, 10, 20} lên `max_tabu` |
| `environment_minconf.json` | cấu hình và máy đo |
| `figures/minconf_*.png` | median số bước, median thời gian, tỉ lệ thành công, ảnh hưởng tabu |

Cột CSV: `N, variant, seed, steps, time, success, restarts`. Với mỗi seed, cả 3 biến thể bắt đầu từ
**cùng một trạng thái khởi tạo** để so sánh công bằng. Mọi nghiệm đều được kiểm tra độc lập bằng `Board.is_valid()`.

Vẽ lại biểu đồ từ CSV có sẵn (không đo lại):

```bash
python -m task1_nqueens.analysis
```

### Notebook

```bash
pip install notebook          # nếu muốn mở bằng trình duyệt; VS Code thì chỉ cần cài extension Jupyter
jupyter notebook task1_nqueens/experiments
```

- `t1_sat.ipynb`: chạy lại ví dụ nhỏ, đọc `sat.csv` thật, vẽ biểu đồ.
- `t1_minconflicts.ipynb`: ví dụ N = 8, bảng kết quả, thống kê restart, biểu đồ, thí nghiệm tabu, chạy lại nhanh, nhận xét.

Notebook tự tìm thư mục `source/` nên mở từ đâu cũng được. Output của mọi cell đã được giữ lại theo yêu cầu đề.

## 4. Các cách chọn biến trong Min-Conflicts

Mỗi bước: chọn một **hàng** đang xung đột, rồi dời quân hậu của hàng đó về **cột ít xung đột nhất** (hòa thì chọn ngẫu nhiên).

| `mode` | Cách chọn hàng xung đột | Ý tưởng |
|---|---|---|
| `standard` | ngẫu nhiên | Min-Conflicts chuẩn (Lecture 08) |
| `max_tabu` | hàng có **nhiều xung đột nhất**, bỏ qua các hàng vừa chọn gần đây (tabu list) | sửa chỗ tệ nhất trước, tabu để không bị lặp |
| `roulette` | ngẫu nhiên có trọng số = số xung đột | ưu tiên hàng xung đột nhiều nhưng vẫn ngẫu nhiên |

Tham số: `tabu_size` (độ dài tabu list), `restart_after` (số bước không cải thiện tổng xung đột trước khi
khởi tạo lại bàn cờ; `None` = không restart), `max_steps`.

`ConflictBoard` lưu số quân theo hàng và hai đường chéo nên tính số xung đột của một ô trong O(1).

## 5. Tóm tắt kết quả đo

Số liệu đầy đủ nằm trong `data/measured/` và notebook.

**SAT (Glucose3)**: N = 4..64 đều giải được; số clause tăng theo O(N³) (80 clause ở N = 4, 428 800 ở N = 64).
Thời gian giải rất nhỏ (cỡ micro-giây đến vài trăm mili-giây) và dao động nhẹ giữa các N lớn do tính chất tìm kiếm của SAT.

**Min-Conflicts (30 seed)**:
- Không restart có thể bị kẹt cực trị cục bộ (ví dụ N = 8: `max_tabu` 4/30 lần, `roulette` 2/30 lần; N = 16: `standard` 2/30 lần).
  Có restart thì mọi cấu hình đạt 100%.
- `max_tabu` ít bước hơn `standard` khoảng 34-57% ở mọi N và ổn định hơn; `roulette` gần như ngang `standard`.
- `tabu_size = 0` kém rõ rệt so với `tabu_size >= 2`; từ 2 đến 20 gần như không khác nhau.
- Với các dòng có thất bại, mean số bước bị kéo lên bởi lần hết ngân sách 20000 bước; hãy đọc **median** và **tỉ lệ thành công**.

## 6. Lưu ý về môi trường đo

- SAT (`sat*.csv`, `environment.json`): đo trên Windows 10, Python 3.14, `python-sat 1.9.dev17`.
- Min-Conflicts (`minconf*.csv`, `environment_minconf.json`): đo trên Linux, Python 3.13.
- Số bước và tỉ lệ thành công của Min-Conflicts **tái lập được** nhờ seed cố định; **thời gian** phụ thuộc máy nên chạy lại
  sẽ ra con số khác, nhưng xu hướng so sánh giữa các biến thể không đổi.
- Biểu diễn nghiệm thống nhất: `Board.columns[row] = col`; `ConflictBoard` kế thừa `Board` và dùng chung `is_valid()`.
  Min-Conflicts coi mỗi **hàng** là một biến.

## 7. Xử lý sự cố

| Lỗi | Cách xử lý |
|---|---|
| `ModuleNotFoundError: task1_nqueens` | Chạy từ thư mục `source/` (chứa `task1_nqueens/`), dùng `python -m task1_nqueens.<module>` |
| `ImportError: attempted relative import` | Không chạy file trực tiếp; dùng `python -m ...` như trên |
| `ModuleNotFoundError: pysat` | `pip install -r task1_nqueens/requirement.txt` |
| Notebook không tìm thấy kernel | `pip install ipykernel`, rồi chọn kernel Python của `.venv` |
