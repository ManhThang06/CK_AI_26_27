# Interface Agent (Task 2.3) - de xuat de nhom ky duyet

Nguon su that la engine cua C (`task2_tank/engine/`). GUI va plugin KHONG co engine rieng.

| Muc | Quy dinh |
|---|---|
| Lop agent | co `choose_action(self, state)`; nen ke thua `task2_tank.agents.base_agent.Agent` |
| Dau vao | `GameState` (ban sao, agent khong the sua state that). `state.player()` = 0 (MAX, tank 1) hoac 1 (MIN, tank 2) |
| Dau ra | 1 gia tri `Action` (MOVE_UP, MOVE_DOWN, MOVE_LEFT, MOVE_RIGHT, FIRE, STAY) |
| Thu tu luot | Moi cycle 2 ply: MAX chon truoc (state.pending luu lai), MIN chon sau, roi engine xu ly ca cycle |
| Thoi gian | 1.0 giay / nuoc (mac dinh, doi duoc trong `load_agent`) |
| Thong ke (tuy chon) | thuoc tinh `nodes`, `last_depth` (xem `Agent`) de thuc nghiem 2.2 |
| Loi | exception / qua gio / tra sai kieu -> STAY + ghi log; 3 loi lien tiep -> agent bi bo qua |
| Nap | duong dan file `.py` HOAC `"module:Class"` (cho agent dung import tuong doi, vd `task2_tank.algorithms.agents:AlphaBetaAgent`) |

Gioi han da biet: timeout dung thread, khong the giet han thread cua agent bi treo (no chay ngam den khi xong). Du cho do an; ghi vao bao cao muc 2.3.

# Dong CSV thuc nghiem Task 1.3
`N,variant,seed,steps,time,success` - moi dong 1 lan chay (khop `analysis.py` cua C). Bieu dien loi giai: `state[cot] = hang`
(Board cua D/A dung `columns[hang] = cot`; bai toan doi xung nen `Board.is_valid` cua D/A van kiem tra duoc loi giai nay).
