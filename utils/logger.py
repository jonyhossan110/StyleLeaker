from __future__ import annotations

import sys
from typing import Any, Iterable, Optional

from colorama import Fore, Style, init

try:
    from tqdm import tqdm  # type: ignore
except ImportError:
    tqdm = None  # type: ignore

init(autoreset=True)

LOG_FORMATS = {
    'INFO': Fore.CYAN,
    'SUCCESS': Fore.GREEN,
    'WARNING': Fore.YELLOW,
    'ERROR': Fore.RED,
    'FOUND': Fore.MAGENTA + Style.BRIGHT,
}


class Logger:
    """Colored console logger for StyleLeaker."""

    def __init__(self, verbose: bool = False) -> None:
        self.verbose = verbose

    def _print(self, label: str, message: str) -> None:
        color = LOG_FORMATS.get(label, Fore.WHITE)
        line = f"[{color}{label}{Style.RESET_ALL}] {message}"
        try:
            print(line)
        except UnicodeEncodeError:
            # Fallback for Windows consoles with limited encodings (e.g., cp1252).
            encoding = (sys.stdout.encoding or 'utf-8')
            safe_line = line.encode(encoding, errors='replace').decode(encoding, errors='replace')
            print(safe_line)

    def info(self, message: str) -> None:
        self._print('INFO', message)

    def success(self, message: str) -> None:
        self._print('SUCCESS', message)

    def warning(self, message: str) -> None:
        self._print('WARNING', message)

    def error(self, message: str) -> None:
        self._print('ERROR', message)

    def found(self, message: str) -> None:
        self._print('FOUND', message)

    def debug(self, message: str) -> None:
        if self.verbose:
            self._print('INFO', message)

    def progress(self, iterable: Iterable, desc: str = 'Processing') -> Iterable:
        if tqdm is None:
            self.warning('tqdm is not installed; falling back to a simple iterator')
            return iterable
        return tqdm(iterable, desc=desc, unit='item', file=sys.stdout)
