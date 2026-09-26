# SPDX-FileCopyrightText: 2025-2026 Yuchen Wang
# SPDX-License-Identifier: GPL-3.0-only
"""Deterministic launcher used by start_ui.bat (run Python in isolated mode)."""
import argparse
import json
from pathlib import Path
import runpy
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
# -I deliberately excludes the script directory. Only add our own source paths.
sys.path.insert(0, str(ROOT / 'tools'))
from check_environment import collect_report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true', help='Check startup without opening the UI.')
    parser.add_argument('--no-pause', action='store_true', help='Used by automated launcher checks.')
    args = parser.parse_args()
    output = ROOT / 'runtime/startup'
    output.mkdir(parents=True, exist_ok=True)
    report = collect_report()
    (output / 'last_check.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    if not report['passed']:
        print('Startup checks failed. No system-Python fallback was attempted.', file=sys.stderr)
        for error in report['errors']:
            print('  - ' + error, file=sys.stderr)
        print('See runtime/startup/last_check.json and docs for environment setup.', file=sys.stderr)
        return 1
    if args.check:
        print('PASS: isolated project environment, locked dependencies and MATLAB installation.')
        print('License availability requires a real MATLAB calculation.')
        return 0
    sys.path.insert(0, str(ROOT / 'src'))
    sys.argv = [str(ROOT / 'src/login.py')]
    runpy.run_path(sys.argv[0], run_name='__main__')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception:
        detail = traceback.format_exc()
        print(detail, file=sys.stderr)
        try:
            output = ROOT / 'runtime/startup'
            output.mkdir(parents=True, exist_ok=True)
            (output / 'last_error.log').write_text(detail, encoding='utf-8')
        except OSError:
            pass
        sys.exit(1)
