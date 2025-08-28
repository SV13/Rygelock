# utils/resource_path.py
import os, sys
from pathlib import Path

def base_dir() -> str:
    # Works for dev and PyInstaller
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS  # type: ignore[attr-defined]
    # fall back to project root (adjust if you run from a submodule)
    return str(Path(__file__).resolve().parents[1])

def resource_path(rel: str) -> str:
    return os.path.join(base_dir(), rel)
