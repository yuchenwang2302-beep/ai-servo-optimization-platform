"""Locations shared by the paper plotting scripts."""
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUTPUT = Path(os.environ.get("PAPER_FIGURE_OUTPUT", str(ROOT / "output"))).resolve()
OUTPUT.mkdir(parents=True, exist_ok=True)
