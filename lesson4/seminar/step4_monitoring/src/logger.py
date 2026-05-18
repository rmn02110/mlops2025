import json
import os
from datetime import datetime

try:
    from colorama import Fore, Style, init

    init()
except ImportError:

    class Fore:
        GREEN = YELLOW = RED = ""

    class Style:
        RESET_ALL = ""


COLORS = {"green": Fore.GREEN, "yellow": Fore.YELLOW, "red": Fore.RED}


class Logger:
    def __init__(self, log_file: str, colors: bool = True):
        self.log_file = log_file
        self.colors = colors
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

    def log(self, level: str, message: str, **data):
        record = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "level": level,
            "message": message,
            **data,
        }
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        color = COLORS.get(level.lower(), "") if self.colors else ""
        print(f"{color}{level.upper()}: {message} {data}{Style.RESET_ALL}")
