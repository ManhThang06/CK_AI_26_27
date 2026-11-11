class KakuroChecker:
    """
    Bo kiem tra doc lap loi giai Kakuro CSP.
    Cau truc clues: danh sach cac tuple (clue_sum, [(r1, c1), (r2, c2), ...])
    Cau truc assignment: dict {(r, c): value} cho moi o trang.
    """

    def __init__(self, white_cells, clues):
        self.white_cells = list(white_cells)
        self.clues = list(clues)

    def check_solution(self, assignment):
        # 1. Kiem tra day du va dung mien gia tri {1..9} (Domain Check)
        for cell in self.white_cells:
            if cell not in assignment or assignment[cell] is None:
                return False, f"O trang {cell} chua duoc dien gia tri"
            val = assignment[cell]
            if not isinstance(val, int) or not (1 <= val <= 9):
                return False, f"Gia tri {val} tai o {cell} nam ngoai mien {{1..9}}"

        # 2. Kiem tra rang buoc Alldiff va Sum tren tung Run
        for clue_sum, run_cells in self.clues:
            values = [assignment[c] for c in run_cells]

            # Alldiff: khong duoc co 2 so trung nhau trong cung 1 run
            if len(values) != len(set(values)):
                return False, f"Vi pham Alldiff tai run {run_cells}: {values}"

            # Sum: tong cac so phai bang chinh xac con so goi y (clue_sum)
            if sum(values) != clue_sum:
                return False, f"Sai tong tai run {run_cells}: tong={sum(values)} != clue={clue_sum}"

        return True, "Loi giai Kakuro hop le 100%"
# --- Unit Tests chung minh checker.py bat loi chinh xac ---
def run_checker_unit_tests():
    # Gia lap 1 bang Kakuro nho gom 4 o trang
    white_cells = [(1, 1), (1, 2), (2, 1), (2, 2)]
    clues = [
        (4, [(1, 1), (1, 2)]),   # Hang 1: tong = 4
        (11, [(2, 1), (2, 2)]),  # Hang 2: tong = 11
        (3, [(1, 1), (2, 1)]),   # Cot 1: tong = 3
        (12, [(1, 2), (2, 2)]),  # Cot 2: tong = 12
    ]
    checker = KakuroChecker(white_cells, clues)
    # Test 1: Bang giai dung ((1,1)=1, (1,2)=3, (2,1)=2, (2,2)=9)
    valid_assign = {(1, 1): 1, (1, 2): 3, (2, 1): 2, (2, 2): 9}
    ok, msg = checker.check_solution(valid_assign)
    assert ok is True, msg
    print("Test 1 (Bang hop le):", msg)
    # Test 2: Bang dien thieu o
    missing_assign = {(1, 1): 1, (1, 2): 3, (2, 1): 2}
    ok, msg = checker.check_solution(missing_assign)
    assert ok is False
    print("Test 2 (Bat loi thieu o):", msg)
    # Test 3: Bang trung so trong cung 1 run (2 + 2 = 4)
    dup_assign = {(1, 1): 2, (1, 2): 2, (2, 1): 1, (2, 2): 9}
    ok, msg = checker.check_solution(dup_assign)
    assert ok is False
    print("Test 3 (Bat loi trung so Alldiff):", msg)
    # Test 4: Bang cong sai tong
    wrong_sum_assign = {(1, 1): 1, (1, 2): 4, (2, 1): 2, (2, 2): 9}
    ok, msg = checker.check_solution(wrong_sum_assign)
    assert ok is False
    print("Test 4 (Bat loi sai tong Sum):", msg)
    print("-> Tat ca Unit Tests cua KakuroChecker: PASS")
if __name__ == "__main__":
    run_checker_unit_tests()