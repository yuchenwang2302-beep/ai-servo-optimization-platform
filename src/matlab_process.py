# SPDX-FileCopyrightText: 2025-2026 Yuchen Wang
# SPDX-License-Identifier: GPL-3.0-only
"""Track one owned Windows process without matching names or reusing a PID."""
from i18n import tr
import ctypes
from ctypes import wintypes


class OwnedWindowsProcess:
    def __init__(self, pid):
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        self.kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self.kernel.OpenProcess.restype = wintypes.HANDLE
        self.kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        self.kernel.WaitForSingleObject.restype = wintypes.DWORD
        self.kernel.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
        self.kernel.TerminateProcess.restype = wintypes.BOOL
        self.kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        self.kernel.CloseHandle.restype = wintypes.BOOL
        # The retained handle identifies this exact process, even if its PID is
        # subsequently reused. No other MATLAB sessions are enumerated or closed.
        self.handle = self.kernel.OpenProcess(0x00100000 | 0x0001, False, int(pid))
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())

    def close(self, wait_ms=10000):
        """Wait for normal exit; terminate only this owned process if it hangs."""
        forced = False
        try:
            state = self.kernel.WaitForSingleObject(self.handle, wait_ms)
            if state == 258:  # WAIT_TIMEOUT
                if not self.kernel.TerminateProcess(self.handle, 1):
                    raise ctypes.WinError(ctypes.get_last_error())
                forced = True
                state = self.kernel.WaitForSingleObject(self.handle, 5000)
            if state != 0:
                raise RuntimeError(tr('本次 MATLAB 后台进程未能退出。'))
            return forced
        finally:
            self.kernel.CloseHandle(self.handle)
            self.handle = None
