## Set up môi trường
 ```bash 
 pip install -r task3_kakuro/requirements.txt
 ```

## Task1

# Giải bằng Glucose3 và đo theo kích thước bàn
```bash
python -m task1_nqueens.sat_solver 4

python -m task1_nqueens.sat_experiment --ns 4 8 16 32 64 --repeats 5 --output ./task1_nqueens/demo_results/sat
```

## Thực nghiệm

```bash
python -m task1_nqueens.sat_experiment --repeats 5 --output ./task1_nqueens/demo_results/sat_full
```
## So sánh Min-Conflicts với heuristic chọn biến

```bash
python -X utf8 -m task1_nqueens.mc_experiment --ns 8 64 --seeds 30 --output ./task1_nqueens/demo_results/minconf
```

```bash
python -X utf8 -m task1_nqueens.mc_experiment --output ./task1_nqueens/demo_results/minconf_full
```


## Task2

# GUI
```bash
python task2_tank/run_gui.py
```

# kiểm tra nhanh

```bash
python -m task2_tank.experiments.compare_search --max-depth 2 --repeats 2

python -m task2_tank.experiments.compare_search --max-depth 3 --repeats 2
```

## Task3

# Chạy test
```bash
python -m task3_kakuro test
```

# Giải map
```bash
python -m task3_kakuro solve task3_kakuro/puzzles/assignment_5x5.json
python -m task3_kakuro solve task3_kakuro/puzzles/assignment_9x9.json
```
# So sánh heuristic
```bash
python -m task3_kakuro bench --repeat 20
```

# GUI
```bash
python -m task3_kakuro.ui.app
```
