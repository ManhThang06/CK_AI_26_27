# Heuristic chon bien cho Min-Conflicts (1.3)

Ban chuan (Lec 08 tr.30): chon NGAU NHIEN 1 bien dang xung dot, gan gia tri it xung dot nhat (hoa thi ngau nhien).
Ban de xuat chi doi buoc **chon bien**; chon gia tri van nhu ban chuan, de so sanh cong bang.

| Ung vien | Y tuong | Ly do | Rui ro |
|---|---|---|---|
| `max_tabu` | Chọn cột nhiều xung đột nhất trong các cột ngoài danh sách tabu, phá hòa ngẫu nhiên | Ưu tiên biến nhiều xung đột, hạn chế chọn lại cột gần đây | Tabu trên cột chưa loại được mọi vòng lặp trạng thái. Nới tabu khi không còn cột phù hợp. |
| `roulette` | Chon cot xung dot voi xac suat ti le so xung dot | Uu tien cot te nhung van giu ngau nhien de thoat cuc tri dia phuong | Gan nhu bang ban chuan khi xung dot deu nhau |

Cách đo dùng 30 seed cho mỗi N, cùng trạng thái ban đầu và ngân sách 20.000 bước giữa các biến thể.
Tỷ lệ thành công được báo cáo cùng trung vị, trung bình, độ lệch chuẩn số bước và thời gian trung bình trên mọi lần chạy.
Các lần thất bại được tính đủ ngân sách, thống nhất với `analysis.py` của Quỳnh. Thời gian gồm khởi tạo và tìm kiếm.
Xem kết quả chạy lại trong `experiments/t1_minconflicts.ipynb` và hai CSV. Hiệu quả phụ thuộc N, biến thể và cơ chế khởi động lại.

## Vi sao co that bai, va cach khac phuc
Mỗi bước thay đổi một biến và chọn giá trị ít xung đột nhất. Thuật toán có thể đi ngang qua plateau hoặc lặp lại trạng thái.
Hết ngân sách bước chỉ xác nhận lần chạy chưa tìm được nghiệm. Giá trị h = 1 chưa đủ để kết luận không thể thoát khỏi vùng đang xét.
Khởi động lại ngẫu nhiên theo Lecture 06 tạo bàn cờ mới sau `restart_after` bước không cải thiện kỷ lục của lần khởi động hiện tại.
Đây là cấu hình bổ sung, được so sánh riêng với bản mặc định không khởi động lại. Tỷ lệ thành công được giới hạn trong các seed đã thử.
