# Demo Task 1 – N-Queens

Demo theo ba yêu cầu của đề: mô hình hóa logic mệnh đề và sinh CNF, giải bằng Glucose3, rồi so sánh các cách chọn biến của Min-Conflicts.

## Chuẩn bị

Giải nén `task1_nqueens.zip`. Mở terminal tại **thư mục cha chứa `task1_nqueens/`**. Trong gói nộp, đó thường là `source/`. Các lệnh bên dưới đều chạy từ thư mục cha này.

**Windows (PowerShell)**

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r task1_nqueens/requirement.txt
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r task1_nqueens/requirement.txt
```

Trên Windows, dùng `.venv/Scripts/python.exe` thay cho `python` trong các lệnh demo nếu chưa kích hoạt môi trường ảo. Chạy theo cú pháp `python -m task1_nqueens.<module>` để các import trong gói hoạt động.

## 1. Mô hình hóa và sinh CNF

```bash
python -c "from task1_nqueens.cnf_encoder import CNFEncoder; clauses = CNFEncoder(4).encode(); print('Clauses:', len(clauses)); print('First row:', clauses[0]); print('First exclusion pair:', clauses[4])"
```

**Khi demo:** Chỉ vào `CNFEncoder.encode()` trong `cnf_encoder.py`. Với bàn 4×4, mỗi ô là một biến Boolean. Mệnh đề `[1, 2, 3, 4]` yêu cầu ít nhất một ô ở hàng đầu có hậu. Mệnh đề `[-1, -2]` cấm đặt hai hậu cùng lúc ở hai ô đầu. Bộ sinh áp dụng quy tắc cấm theo cặp cho từng hàng, cột và đường chéo. Kết quả là **16 biến và 80 mệnh đề**.

## 2. Giải bằng Glucose3 và đo theo kích thước bàn

```bash
python -m task1_nqueens.sat_solver 4
python -m task1_nqueens.sat_experiment --ns 4 8 16 32 --repeats 5 --output demo_results/sat
```

**Khi demo:** Lệnh đầu in kết quả `sat` và bàn cờ nghiệm. `SATSolver` nạp CNF vào Glucose3, giải mã nghiệm và kiểm tra bàn cờ bằng `Board.is_valid()`. Với lệnh thứ hai, mở `demo_results/sat/sat_summary.csv` để chỉ hai cột `num_clauses` và `mean_s`. `mean_s` là thời gian giải trung bình tính bằng **giây**. `sat.csv` lưu từng lượt và tách riêng thời gian sinh CNF, nạp CNF và gọi bộ giải.

Để trình bày đủ dãy kích thước, mở [kết quả đã lưu](data/measured/sat_summary.csv) hoặc chạy lại:

```bash
python -m task1_nqueens.sat_experiment --repeats 5 --output demo_results/sat_full
```

Dùng biểu đồ [số mệnh đề](data/measured/figures/sat_clauses.png) và [thời gian giải](data/measured/figures/sat_time.png) khi trình bày. Ví dụ, số mệnh đề tăng từ **80** ở N = 4 lên **428.800** ở N = 64. Thời gian đo lại phụ thuộc vào máy.

## 3. So sánh Min-Conflicts với heuristic chọn biến

```bash
python -X utf8 -m task1_nqueens.mc_experiment --ns 8 64 --seeds 30 --output demo_results/minconf
```

**Khi demo:** Trong bản code này, **mỗi hàng là một biến**, giá trị là cột đặt hậu. Mỗi bước chọn một hàng đang xung đột, sau đó chọn cột có ít xung đột nhất cho quân hậu của hàng đó. Cả ba cách dùng chung quy tắc chọn cột và cùng bàn khởi tạo cho một cặp kích thước và seed.

| Cấu hình | Cách chọn hàng đang xung đột |
|---|---|
| `standard` | Chọn ngẫu nhiên đều. |
| `max_tabu` | Ưu tiên hàng xung đột nhiều nhất trong các hàng ngoài danh sách tabu. Nếu tất cả đều nằm trong danh sách, xét lại tất cả các hàng đang xung đột. |
| `roulette` | Chọn ngẫu nhiên theo trọng số là số xung đột của mỗi hàng. |

Đọc bảng **không restart** trong terminal. Chỉ hai chỉ số `med_st` (trung vị số bước) và `succ(%)` (tỷ lệ giải được). Trong [dữ liệu nhóm đã lưu](data/measured/minconf.csv), tại N = 64, `standard` có trung vị **111 bước**, `max_tabu` có **69,5 bước**, cả hai giải **30/30** lượt. Tại N = 8, `max_tabu` có trung vị **14,5 bước** nhưng chỉ giải **26/30** lượt, nên cần đọc số bước cùng tỷ lệ thành công.

Lệnh trên cũng xuất `minconf_restart.csv` và `minconf_tabu.csv` để xem riêng tác động của restart và độ dài tabu. Muốn chạy lại toàn bộ kích thước của nhóm:

```bash
python -X utf8 -m task1_nqueens.mc_experiment --output demo_results/minconf_full
```

Có thể mở [notebook SAT](experiments/t1_sat.ipynb) và [notebook Min-Conflicts](experiments/t1_minconflicts.ipynb) trong VS Code bằng kernel của `.venv`. Giữ output các cell khi đóng gói bài nộp.

