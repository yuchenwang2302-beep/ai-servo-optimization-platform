"""Redraw the numerical paper figures from the recorded CSV files."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
SCRIPTS = {"3": "fig03_response.py", "4": "fig04_archive.py", "5": "fig05_selected.py"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("figure", choices=[*SCRIPTS, "all"], nargs="?", default="all")
    parser.add_argument("--output", type=Path, default=ROOT / "output")
    args = parser.parse_args()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    env["PAPER_FIGURE_OUTPUT"] = str(args.output.resolve())
    for choice in SCRIPTS if args.figure == "all" else [args.figure]:
        subprocess.run([sys.executable, str(ROOT / "scripts" / SCRIPTS[choice])], env=env, check=True)
    print("Saved figures in", args.output.resolve())


if __name__ == "__main__":
    main()
