import csv
import json
from abc import ABC, abstractmethod
from pathlib import Path


class Experiment(ABC):
    """Lớp cha của các thực nghiệm: quản lý thư mục xuất, ghi CSV và file môi trường."""

    def __init__(self, output):
        self.output = Path(output)

    def save_csv(self, rows, name, fieldnames=None):
        self.output.mkdir(parents=True, exist_ok=True)
        with (self.output / name).open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames or list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    def save_environment(self, name, info):
        self.output.mkdir(parents=True, exist_ok=True)
        (self.output / name).write_text(json.dumps(info, indent=2, ensure_ascii=False),
                                        encoding="utf-8")

    @abstractmethod
    def run(self):
        """Chạy thực nghiệm, ghi kết quả vào `self.output`."""
