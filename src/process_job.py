# SPDX-FileCopyrightText: 2025-2026 Yuchen Wang
# SPDX-License-Identifier: GPL-3.0-only
"""A private Windows job contains a run's process tree, including MATLAB startup.

The launcher is created suspended, assigned to this job, then resumed. This
also contains the base Python process spawned by Windows' venv redirector.
No processes are discovered by executable name; other MATLAB sessions are
never targeted.
"""
import ctypes
from i18n import tr
from ctypes import wintypes as w
import time


class BasicLimits(ctypes.Structure):
    _fields_ = [('process_time', ctypes.c_int64), ('job_time', ctypes.c_int64),
                ('flags', w.DWORD), ('min_ws', ctypes.c_size_t), ('max_ws', ctypes.c_size_t),
                ('active_limit', w.DWORD), ('affinity', ctypes.c_size_t),
                ('priority', w.DWORD), ('scheduling', w.DWORD)]


class IoCounters(ctypes.Structure):
    _fields_ = [(name, ctypes.c_uint64) for name in ('read_ops', 'write_ops', 'other_ops',
                                                   'read_bytes', 'write_bytes', 'other_bytes')]


class ExtendedLimits(ctypes.Structure):
    _fields_ = [('basic', BasicLimits), ('io', IoCounters),
                ('process_memory', ctypes.c_size_t), ('job_memory', ctypes.c_size_t),
                ('peak_process_memory', ctypes.c_size_t), ('peak_job_memory', ctypes.c_size_t)]


class Accounting(ctypes.Structure):
    _fields_ = [(name, ctypes.c_int64) for name in ('user', 'kernel', 'period_user', 'period_kernel')]
    _fields_ += [(name, w.DWORD) for name in ('faults', 'total', 'active', 'terminated')]


class ThreadEntry(ctypes.Structure):
    _fields_ = [('size', w.DWORD), ('usage', w.DWORD), ('thread', w.DWORD),
                ('owner', w.DWORD), ('base_priority', w.LONG), ('delta_priority', w.LONG), ('flags', w.DWORD)]


class ProcessJob:
    def __init__(self):
        self.api = ctypes.WinDLL('kernel32', use_last_error=True)
        signatures = {
            'CreateJobObjectW': ([ctypes.c_void_p, w.LPCWSTR], w.HANDLE),
            'SetInformationJobObject': ([w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD], w.BOOL),
            'QueryInformationJobObject': ([w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD, ctypes.c_void_p], w.BOOL),
            'OpenProcess': ([w.DWORD, w.BOOL, w.DWORD], w.HANDLE),
            'AssignProcessToJobObject': ([w.HANDLE, w.HANDLE], w.BOOL),
            'IsProcessInJob': ([w.HANDLE, w.HANDLE, ctypes.POINTER(w.BOOL)], w.BOOL),
            'TerminateJobObject': ([w.HANDLE, w.UINT], w.BOOL),
            'CloseHandle': ([w.HANDLE], w.BOOL),
            'CreateToolhelp32Snapshot': ([w.DWORD, w.DWORD], w.HANDLE),
            'Thread32First': ([w.HANDLE, ctypes.POINTER(ThreadEntry)], w.BOOL),
            'Thread32Next': ([w.HANDLE, ctypes.POINTER(ThreadEntry)], w.BOOL),
            'OpenThread': ([w.DWORD, w.BOOL, w.DWORD], w.HANDLE),
            'ResumeThread': ([w.HANDLE], w.DWORD),
            'WaitForSingleObject': ([w.HANDLE, w.DWORD], w.DWORD),
        }
        for name, (args, result) in signatures.items():
            method = getattr(self.api, name)
            method.argtypes, method.restype = args, result
        self.handle = self.api.CreateJobObjectW(None, None)
        self._check(self.handle)
        limits = ExtendedLimits()
        limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE; no breakaway.
        try:
            self._check(self.api.SetInformationJobObject(self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)))
        except Exception:
            self.api.CloseHandle(self.handle)
            self.handle = None
            raise

    @staticmethod
    def _check(value):
        if not value:
            raise ctypes.WinError(ctypes.get_last_error())
        return value

    def assign(self, pid):
        process = self._check(self.api.OpenProcess(0x0100 | 0x0001, False, int(pid)))
        try:
            self._check(self.api.AssignProcessToJobObject(self.handle, process))
        finally:
            self.api.CloseHandle(process)

    def contains(self, pid):
        process = self._check(self.api.OpenProcess(0x1000, False, int(pid)))
        try:
            result = w.BOOL()
            self._check(self.api.IsProcessInJob(process, self.handle, ctypes.byref(result)))
            return bool(result.value)
        finally:
            self.api.CloseHandle(process)

    def resume(self, pid):
        """Resume the one primary thread of the CREATE_SUSPENDED child."""
        snapshot = self.api.CreateToolhelp32Snapshot(4, 0)  # TH32CS_SNAPTHREAD
        if snapshot == ctypes.c_void_p(-1).value:
            self._check(False)
        try:
            entry = ThreadEntry()
            entry.size = ctypes.sizeof(entry)
            found = self.api.Thread32First(snapshot, ctypes.byref(entry))
            while found:
                if entry.owner == pid:
                    thread = self._check(self.api.OpenThread(0x0002, False, entry.thread))
                    try:
                        if self.api.ResumeThread(thread) == 0xffffffff:
                            self._check(False)
                        return
                    finally:
                        self.api.CloseHandle(thread)
                found = self.api.Thread32Next(snapshot, ctypes.byref(entry))
            raise RuntimeError(tr('无法恢复本次计算进程的启动线程。'))
        finally:
            self.api.CloseHandle(snapshot)

    def _process_handles(self):
        """Hold identities before termination; accounting may reach zero before exit signals."""
        capacity = 64
        while True:
            buffer = ctypes.create_string_buffer(8 + ctypes.sizeof(ctypes.c_size_t) * capacity)
            if self.api.QueryInformationJobObject(self.handle, 3, buffer, len(buffer), None):
                break
            if ctypes.get_last_error() != 234 or capacity >= 16384:
                self._check(False)
            capacity *= 2
        count = w.DWORD.from_buffer(buffer, 4).value
        pids = (ctypes.c_size_t * count).from_buffer(buffer, 8)
        handles = []
        for pid in pids:
            process = self.api.OpenProcess(0x00100000, False, pid)
            if process:
                handles.append(process)
        return handles

    def active_count(self):
        info = Accounting()
        self._check(self.api.QueryInformationJobObject(self.handle, 1, ctypes.byref(info), ctypes.sizeof(info), None))
        return info.active

    def terminate(self):
        self._check(self.api.TerminateJobObject(self.handle, 1))

    def close(self):
        if self.handle is None:
            return
        processes = []
        report = {'forced_termination': False, 'active_before_cleanup': None,
                  'remaining_processes': None, 'exit_signals_verified': False}
        try:
            processes = self._process_handles()
            report['active_before_cleanup'] = self.active_count()
            report['retained_process_handles'] = len(processes)
            if report['active_before_cleanup']:
                self.terminate()
                report['forced_termination'] = True
                deadline = time.monotonic() + 5
                while self.active_count() and time.monotonic() < deadline:
                    time.sleep(.05)
                if self.active_count():
                    raise RuntimeError(tr('本次计算进程仍在退出，请查看运行日志。'))
            deadline = time.monotonic() + 5
            for process in processes:
                remaining = max(0, int((deadline - time.monotonic()) * 1000))
                if self.api.WaitForSingleObject(process, remaining) != 0:
                    raise RuntimeError(tr('本次计算的子进程未能按时退出。'))
            report['remaining_processes'] = self.active_count()
            report['exit_signals_verified'] = True
            return report
        finally:
            for process in processes:
                self.api.CloseHandle(process)
            self.api.CloseHandle(self.handle)
            self.handle = None
