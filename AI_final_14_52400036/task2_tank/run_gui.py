"""Chạy GUI Tank Battle:  python run_gui.py  (hoặc python task2_tank/run_gui.py)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from task2_tank.gui.app import main  # noqa: E402

if __name__ == "__main__":
    main()
