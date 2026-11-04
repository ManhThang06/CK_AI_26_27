import runpy
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / "source"))
if len(sys.argv) < 2:
    raise SystemExit("Usage: python run.py MODULE [arguments]")
module = sys.argv.pop(1)
runpy.run_module(module, run_name="__main__", alter_sys=True)