# Task 1.3 - Min-Conflicts của phần B
Chạy từ thư mục `Liem_B` bằng các lệnh sau.
```
python -m task1_nqueens.min_conflicts
python -m task1_nqueens.mc_experiment
python -m unittest discover -s tests -t .
```
Các chế độ gồm `standard` (Lecture 08, trang 30), `max_tabu` và `roulette`.
`standard` chọn ngẫu nhiên biến đang xung đột. Các chế độ đều chọn hàng ít xung đột nhất và phá hòa ngẫu nhiên.
`max_tabu` hạn chế chọn lại các cột gần đây. Khi mọi cột xung đột đều bị hạn chế, điều kiện tabu được nới để tiếp tục tìm kiếm.

Chương trình chỉ dùng thư viện chuẩn Python. Hai CSV được lưu trong `Liem_B/experiments`, gồm bản chuẩn và bản bổ sung khởi động lại ngẫu nhiên.
Số bước, độ lệch chuẩn và thời gian trung bình tính trên mọi lần chạy, kể cả lần hết ngân sách, tương thích với biểu đồ của Quỳnh.
Thời gian gồm khởi tạo bàn cờ và tìm kiếm. Hết ngân sách chỉ cho biết lần chạy chưa tìm được nghiệm.
