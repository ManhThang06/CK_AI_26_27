# Task 3.2 - Checker doc lap + thuc nghiem (phan B)
```
python -m task3_kakuro.checker                              # unit test nhanh cua checker
python -m unittest discover -s task3_kakuro/tests -t .      # test day du (checker + 2 bang trong de)
```
`puzzle_io.load_puzzle` doc file JSON cua de (`puzzles/*.json`) sang (o trang, danh sach run) cho `KakuroChecker`.
`ablation_solver.py` la solver dung cho thuc nghiem 4 cau hinh; notebook: `experiments/t3_kakuro.ipynb`.
