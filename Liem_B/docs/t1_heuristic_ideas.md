# Heuristic chon bien cho Min-Conflicts (1.3)

Ban chuan (Lec 08 tr.30): chon NGAU NHIEN 1 bien dang xung dot, gan gia tri it xung dot nhat (hoa thi ngau nhien).
Ban de xuat chi doi buoc **chon bien**; chon gia tri van nhu ban chuan, de so sanh cong bang.

| Ung vien | Y tuong | Ly do | Rui ro |
|---|---|---|---|
| `max_tabu` (chon lam heuristic chinh) | Chon cot xung dot NHIEU NHAT; hoa thi ngau nhien; cot vua chon nam trong danh sach tabu (do dai `max(2, min(10, N//5))`) mot thoi gian | Sua cot "te nhat" truoc giam h nhanh hon; tabu chong lap lai cung mot cot | Ket o cuc tri dia phuong (h dung yen = 1) -> that bai o N=8 (4/30 lan); khong lien quan do dai tabu (thu 2..6 deu 26-27/30) |
| `roulette` | Chon cot xung dot voi xac suat ti le so xung dot | Uu tien cot te nhung van giu ngau nhien de thoat cuc tri dia phuong | Gan nhu bang ban chuan khi xung dot deu nhau |

Cach do: 30 seed co dinh moi N, cung trang thai khoi tao, cung max_steps = 20000; do ti le thanh cong, trung vi va TB so buoc
(lan thanh cong), thoi gian/lan. Ket qua (xem `experiments/t1_minconflicts.ipynb`): `max_tabu` giam so buoc khoang 30-35%
o N >= 16 nhung thoi gian gan nhu bang ban chuan khi N lon (moi buoc ton hon: phai tinh xung dot cua moi cot).

## Vi sao co that bai, va cach khac phuc
Min-Conflicts chi nhin 1 quan hau moi buoc va gan no vao hang it xung dot nhat. Khi h = 1 (con dung 1 cap an nhau) co
the khong quan nao co nuoc di giam h -> bi **ket o cuc tri dia phuong** (ca "plateau"), lap lai vo han. Them ngau nhien khi
chon cot (thu p = 0.05..0.2) KHONG giup, vi van moi ket o buoc chon gia tri. **Random restart** (Lec 06): sau `restart_after`
buoc khong cai thien ky luc h thi xep lai ban co -> 30/30 thanh cong o moi N, moi variant (xem notebook, bang B).
