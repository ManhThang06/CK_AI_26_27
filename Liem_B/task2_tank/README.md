# Task 2.3 - GUI PyGame + nap agent ngoai (phan B)

Cai: `pip install -r requirement.txt` (pygame). Chay tu thu muc `Liem_B`:

```
python -m task2_tank.gui.app                              # GUI: Q/W chon agent, M chon ban do, ENTER bat dau
python -m unittest discover -s task2_tank/tests -t .      # test plugin + tran dau (khong can pygame)
```

- `engine/` la engine cua C (giu nguyen), `maps/` la ban do cua A.
- `plugin_loader.py`: `load_agent("external_agents/x.py")` hoac `load_agent("module:Class")`; loi/qua gio -> STAY, khong sap game.
- `external_agents/`: `demo_corner_camper.py` (dong vai agent nhom khac), `bad_agent_*.py` (loi co y de test).
- `gui/match.py`: dieu khien van dau, khong phu thuoc pygame; ghi log tran vao `logs/last_match.csv`.
- De dung agent tim kiem cua D: copy thu muc `algorithms/` cua D vao `task2_tank/`, chon trong menu hoac goi
  `load_agent("task2_tank.algorithms.agents:AlphaBetaAgent", horizon=2)`.
- Phim (nguoi choi): mui ten = di, SPACE = ban, S = dung yen.
