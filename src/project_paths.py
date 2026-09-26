# SPDX-FileCopyrightText: 2025-2026 Yuchen Wang
# SPDX-License-Identifier: GPL-3.0-only
"""Paths shared by the GUI and MATLAB, independent of the launch directory."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def data_directory(is_optimization=False):
    path = PROJECT_ROOT / "runtime" / ("optimization" if is_optimization else "identification")
    path.mkdir(parents=True, exist_ok=True)
    return path
