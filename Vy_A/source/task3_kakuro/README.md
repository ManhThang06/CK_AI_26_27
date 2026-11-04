# UI A và solver ghép thử theo tổ hợp của C

Chạy từ Vy_A: `python run.py task3_kakuro.ui.app`.
1: bảng 5×5; 2: bảng 9×9; 3: bảng 5×5 tắt heuristic.
Space: Play/Pause; trái/phải: lùi/tiến; R reset; +/- tốc độ; click ô xem miền và run.

Hai bảng đề được giải bằng solver.py mới, propagation.py theo t3_propagation.docx.
Bảng 9×9 mặc định có quay lui thật; không dùng trace từ solver permutations cũ.
Schema UI giữ nguyên: mỗi event có snapshot domains sau thao tác;
removed là giá trị vừa bị loại; backtrack chứa domains đã phục hồi đầy đủ.

assignment và trail dùng cho thuật toán; snapshot chỉ dùng replay, không sao chép state tìm kiếm mỗi nhánh.
C/D có thể thay solver bằng module chính thức, emit cùng schema.
Xem docs đối chiếu để biết giới hạn bộ lọc và LCV xấp xỉ.