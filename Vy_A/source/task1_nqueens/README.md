# Phần A Task 1, ghép analysis.py của C

Từ `Vy_A`: `python run.py task1_nqueens.sat_solver 8`.
Thực nghiệm: `python run.py task1_nqueens.experiment --repeats 5`.
Số liệu thật: `data/measured/sat.csv`, summary và environment cạnh đó.
`sample_sat.csv`, `sample_minconf.csv` là mẫu gốc C, chưa phải đo thực tế.
Notebook ở `experiments/t1_sat.ipynb` đọc số liệu đo, có output thực thi.
Biểu diễn Board.columns[row]=col, cần thống nhất với D trước khi ghép validator chung.