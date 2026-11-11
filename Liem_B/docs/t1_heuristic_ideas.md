# Task 1.3: Mô hình hóa Min-Conflicts và Đề xuất Heuristic chọn biến
## 1. Biểu diễn trạng thái (Complete-State Formulation)
- **Biến (Variables):** $X = \{X_0, X_1, \dots, X_{N-1}\}$, trong đó $X_c$ biểu diễn vị trí hàng của quân hậu tại cột $c$.
- **Miền giá trị (Domains):** $D(X_c) = \{0, 1, \dots, N-1\}$ với mọi $c \in [0, N-1]$. Cách biểu diễn này tự động thỏa mãn ràng buộc không có 2 quân hậu nào đứng cùng một cột.
- **Đếm xung đột $O(1)$:** Sử dụng 3 mảng đếm số lượng quân hậu trên từng hàng ngang (`row_count`), đường chéo chính (`diag1_count` với chỉ số $r - c + N - 1$) và đường chéo phụ (`diag2_count` với chỉ số $r + c$).

## 2. Các phương pháp chọn biến (Variable Selection Heuristics)
### 2.1. Bản chuẩn (Standard Min-Conflicts - Lec 08 Slide 30)
- **Cơ chế:** Chọn ngẫu nhiên đồng đều (uniform random) một cột $c$ từ tập các cột đang có xung đột (`conflicted_cols`).
- **Nhược điểm:** Không tận dụng được thông tin mức độ nghiêm trọng của xung đột tại mỗi cột, dẫn đến số bước lặp lớn khi $N$ tăng.

### 2.2. Đề xuất 1: Max-Conflict kết hợp Danh sách cấm (Max-Tabu)
- **Ý tưởng:** Ưu tiên chọn cột $c \in \text{conflicted\_cols}$ có số lượng xung đột hiện tại lớn nhất để giảm nhanh hàm mục tiêu $h$.
- **Xử lý kẹt (Plateau / Cycling):** Nếu chỉ chọn cực đại thuần túy, thuật toán dễ bị lặp vô hạn giữa một nhóm nhỏ các cột. Ta duy trì một danh sách `tabu_list` lưu lại $k$ cột vừa mới được chọn gần nhất ($k = \text{tabu\_size}$). Ở mỗi bước, chỉ xét các cột xung đột không nằm trong `tabu_list` (nếu tất cả các cột xung đột đều nằm trong Tabu thì mới nới lỏng để xét toàn bộ).

### 2.3. Đề xuất 2: Chọn theo xác suất tỷ lệ thuận xung đột (Roulette Wheel)
- **Ý tưởng:** Mỗi cột $c \in \text{conflicted\_cols}$ được gán trọng số $w_c = \text{conflicts}(c, \text{state}[c])$. Xác suất cột $c$ được chọn là:
  $$P(c) = \frac{w_c}{\sum_{j \in \text{conflicted\_cols}} w_j}$$
- **Ưu điểm:** Vừa hướng việc tìm kiếm vào các cột nhiều xung đột (exploitation), vừa giữ lại xác suất nhỏ cho các cột ít xung đột để thoát khỏi cực trị địa phương mà không cần bộ nhớ phụ (exploration).

## 3. Thiết kế thực nghiệm và Kết quả (30 Seeds, max_steps = 20000)
- **Phương pháp đo:** Với mỗi kích thước $N \in \{8, 16, 32, 64, 100, 200\}$, chạy lặp 30 seed cố định (`seed = 1..30`). Ở mỗi cặp $(N, \text{seed})$, cả 3 chế độ dùng chung một trạng thái bàn cờ khởi tạo ban đầu (`init_state`) để đảm bảo tính công bằng.
- **Độ đo:** Tỷ lệ thành công (`Success Rate %`), Số bước trung bình (`Avg Steps`), Thời gian chạy trung bình (`Avg Time ms`).

| N | Standard (Steps / Time) | Max-Tabu (Steps / Time) | Roulette (Steps / Time) | Tỷ lệ thành công |
|---:|:---:|:---:|:---:|:---:|
| 8 | 38.53 / 0.197 ms | **18.03 / 0.107 ms** | 45.20 / 0.303 ms | 100.0% |
| 16 | 64.00 / 0.531 ms | **26.70 / 0.269 ms** | 75.40 / 0.744 ms | 100.0% |
| 32 | 74.40 / 1.108 ms | **39.63 / 0.692 ms** | 82.13 / 1.493 ms | 100.0% |
| 64 | 116.20 / 3.386 ms | **59.20 / 2.004 ms** | 108.63 / 3.576 ms | 100.0% |
| 100 | 141.63 / 5.979 ms | **88.17 / 4.450 ms** | 134.17 / 6.836 ms | 100.0% |
| 200 | 198.07 / 17.991 ms | **145.37 / 15.352 ms** | 189.23 / 18.907 ms | 100.0% |

## 4. Nhận xét
- **Max-Tabu** vượt trội hoàn toàn so với bản chuẩn trên mọi kích thước $N$: giảm từ **35% đến 58% số bước di chuyển** và giảm đáng kể thời gian thực thi nhờ giải quyết trực tiếp các quân hậu gây xung đột nhiều nhất mà không bị lặp chu trình.
- **Roulette** bắt đầu cho thấy lợi thế về số bước so với bản chuẩn khi $N \ge 64$, tuy nhiên chi phí tính toán mảng trọng số ở mỗi bước khiến thời gian thực thi (ms) cao hơn nhẹ so với bản chuẩn.