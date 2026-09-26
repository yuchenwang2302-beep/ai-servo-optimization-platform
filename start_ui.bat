@echo off
REM SPDX-FileCopyrightText: 2025-2026 Yuchen Wang
REM SPDX-License-Identifier: GPL-3.0-only
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Project environment is missing. Run tools\setup_environment.ps1 as described in README.md.
    goto failed
)
".venv\Scripts\python.exe" -I -X faulthandler tools\start_ui.py %*
if not "%errorlevel%"=="0" goto failed
exit /b 0
:failed
echo Startup failed. Keep the error above; see runtime\startup for any available diagnostic report.
for %%A in (%*) do if /i "%%~A"=="--no-pause" exit /b 1
pause
exit /b 1
