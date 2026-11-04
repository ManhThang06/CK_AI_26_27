# Phần A — Thảo Vy

Phần N-Queens, giao diện Kakuro và bản đồ Tank tích hợp theo nền Quỳnh-C.
Engine Tank và module thống kê gốc của C được đặt trong bản tích hợp để chạy độc lập.
Code có phần được hỗ trợ bởi AI; việc sử dụng cần tuân theo quy định giảng viên.

## Cài đặt

Yêu cầu Python 3.11. Sau khi clone, mở terminal tại thư mục Vy_A:

```sh
python -m venv .venv
```

Kích hoạt trên Windows PowerShell: `.venv\Scripts\Activate.ps1`.
Trên macOS/Linux: `source .venv/bin/activate`.

```sh
python -m pip install -r requirements.txt
python run.py task1_nqueens.sat_solver 8
python run.py task1_nqueens.experiment
python run.py task3_kakuro.ui.app
```

## Kiểm thử

```sh
python run.py unittest discover -s tests -v
python run.py unittest discover -s source/task2_tank/tests -v
```

Đã chạy đạt 8 test tích hợp và 28 test engine. SAT có 45 lượt từ N=4 đến N=64;
hai bảng Kakuro theo đề đều qua kiểm tra tổng và điều kiện khác nhau từng run.
Số đo trên Windows chưa đại diện cho máy chấm macOS.

## Cấu trúc

- `source/task1_nqueens`: CNF, Glucose3, thống kê C, notebook và dữ liệu đo.
- `source/task2_tank`: engine C, test gốc và các bản đồ dùng chung.
- `source/task3_kakuro`: dữ liệu đề, bộ giải tích hợp thử và giao diện PyGame.
- `tests`: kiểm thử tích hợp phần A.
- `run.py`: chạy module từ thư mục source.

CSV sample là dữ liệu mẫu của C. Số liệu thật ở `source/task1_nqueens/data/measured/`.
Notebook giữ output. Bộ giải Kakuro dùng thử UI, chờ đối chiếu với phần chính thức C/D.
Min-Conflicts, agent/GUI Tank, báo cáo và video cần ghép với các thành viên phụ trách.

## Giao diện Kakuro

Phím 1/2/3 chọn bảng; Space phát/tạm dừng; trái/phải lùi/tiến;
R đặt lại; +/- đổi tốc độ. Bấm ô trắng để xem miền và các run liên quan.
