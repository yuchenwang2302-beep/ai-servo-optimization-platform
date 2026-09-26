# SPDX-FileCopyrightText: 2025-2026 Yuchen Wang
# SPDX-License-Identifier: GPL-3.0-only
"""Run records and bounded retention. Only recognized, finished runs are removed."""
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import stat
import time

from project_paths import PROJECT_ROOT

TERMINAL = {'succeeded', 'failed', 'cancelled', 'timed_out'}
RUN_NAME = re.compile(r'^\d{8}_\d{6}_[0-9a-f]{8}$')
DEFAULT_POLICY = {'enabled': True, 'days': 30, 'keep_latest': 20, 'cache_days': 7}


def linked(path):
    if path.is_symlink():
        return True
    return os.name == 'nt' and bool(path.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)


class RunStore:
    def __init__(self, root=None):
        candidate = Path(root or PROJECT_ROOT / 'runtime').absolute()
        if candidate.exists() and linked(candidate):
            raise ValueError('Runtime directory must not be a link or junction.')
        self.root = candidate.resolve()

    def safe(self, path):
        path = Path(path).absolute()
        if not path.is_relative_to(self.root) or path == self.root:
            return False
        for parent in (path, *path.parents):
            if parent == self.root:
                break
            if os.path.lexists(parent) and linked(parent):
                return False
        return path.resolve().is_relative_to(self.root)

    def read_json(self, path):
        if not self.safe(path):
            return {}
        try:
            value = path.read_text(encoding='utf-8')
            result = json.loads(value) if len(value) < 1_000_000 else {}
            return result if isinstance(result, dict) else {}
        except (OSError, ValueError):
            return {}

    @contextmanager
    def locked(self):
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / '.maintenance.lock'
        if not self.safe(path):
            raise ValueError('Unsafe maintenance lock path.')
        with path.open('a+b') as lock:
            lock.seek(0, 2)
            if not lock.tell():
                lock.write(b'0'); lock.flush()
            lock.seek(0)
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            try:
                yield
            finally:
                if os.name == 'nt':
                    lock.seek(0)
                    msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)

    def policy(self):
        saved = self.read_json(self.root / 'retention.json')
        result = dict(DEFAULT_POLICY)
        if isinstance(saved, dict):
            result['enabled'] = saved.get('enabled', True) is not False
            days = saved.get('days', 30)
            if isinstance(days, int) and 7 <= days <= 3650:
                result['days'] = days
        return result

    def save_policy(self, enabled, days):
        if not 7 <= int(days) <= 3650:
            raise ValueError('Retention must be between 7 and 3650 days.')
        with self.locked():
            self._write(self.root / 'retention.json', dict(DEFAULT_POLICY, enabled=bool(enabled), days=int(days)))

    def _write(self, path, value):
        temporary = path.with_suffix(path.suffix + '.next')
        if not self.safe(path) or not self.safe(temporary):
            raise ValueError('Unsafe metadata path.')
        temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
        temporary.replace(path)

    def records(self):
        records = []
        for mode in ('identification', 'optimization'):
            folder = self.root / mode
            if not self.safe(folder) or not folder.is_dir():
                continue
            for path in folder.iterdir():
                if not RUN_NAME.fullmatch(path.name) or not self.safe(path) or not path.is_dir():
                    continue
                request = self.read_json(path / 'request.json')
                state = self.read_json(path / 'run_state.json')
                if (not isinstance(request.get('algorithm'), str) or not request['algorithm']
                        or not isinstance(request.get('params', {}), dict)
                        or not isinstance(state.get('state'), str)):
                    continue
                if '_scenario' in request.get('params', {}):
                    continue  # Fault-injection fixtures are not user experiments.
                try:
                    created = datetime.strptime(path.name[:15], '%Y%m%d_%H%M%S').timestamp()
                    # A record is old only after its final status and request are old too.
                    touched = max(created, (path / 'request.json').stat().st_mtime,
                                  (path / 'run_state.json').stat().st_mtime)
                except (ValueError, OSError):
                    continue
                records.append({'path': path, 'mode': mode, 'created': created, 'touched': touched,
                                'request': request, 'state': state, 'archived': (path / 'archive.json').exists()})
        return sorted(records, key=lambda record: record['created'], reverse=True)

    def archive(self, path, enabled):
        with self.locked():
            record = next((r for r in self.records() if r['path'] == Path(path)), None)
            if record is None or record['state'].get('state') not in TERMINAL:
                raise ValueError('Only a finished run can be archived.')
            marker = record['path'] / 'archive.json'
            if not self.safe(marker):
                raise ValueError('Unsafe archive path.')
            if enabled:
                self._write(marker, {'archived_at': datetime.now(timezone.utc).isoformat()})
            else:
                marker.unlink(missing_ok=True)

    def tree_size(self, path):
        """Verify every descendant before a recursive deletion; never follow links."""
        if not self.safe(path):
            raise ValueError('Unsafe cleanup path.')
        if path.is_file():
            return path.stat().st_size
        total = 0
        for base, directories, files in os.walk(path, followlinks=False):
            for name in directories + files:
                child = Path(base) / name
                info = child.lstat()
                if stat.S_ISLNK(info.st_mode) or (os.name == 'nt' and info.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT):
                    raise ValueError('Cleanup target contains a link or junction.')
                if stat.S_ISREG(info.st_mode):
                    total += info.st_size
        return total

    def cleanup(self, *, now=None, force=False, cancelled=lambda: False):
        summary = {'removed_runs': 0, 'removed_caches': 0, 'freed_bytes': 0, 'errors': []}
        with self.locked():
            policy = self.policy()
            if not force and not policy['enabled']:
                return summary
            now = time.time() if now is None else now
            records = self.records()
            eligible = [r for r in records if r['state'].get('state') in TERMINAL and not r['archived']]
            protected = {r['path'] for r in eligible[:policy['keep_latest']]}
            for record in eligible:
                if cancelled():
                    break
                path = record['path']
                try:
                    # Recheck metadata immediately before deleting. Other history actions share this lock.
                    current = self.read_json(path / 'run_state.json')
                    if (path / 'archive.json').exists() or not isinstance(current, dict) or current.get('state') not in TERMINAL:
                        continue
                    age = now - record['touched']
                    if path not in protected and age > policy['days'] * 86400:
                        size = self.tree_size(path)
                        shutil.rmtree(path)
                        summary['removed_runs'] += 1
                        summary['freed_bytes'] += size
                    elif age > policy['cache_days'] * 86400:
                        # These are rebuildable Simulink caches, not MAT curves, logs or result.npz.
                        targets = list(path.glob('*.slxc'))
                        if (path / 'slprj').exists():
                            targets.append(path / 'slprj')
                        for target in targets:
                            size = self.tree_size(target)
                            if target.is_dir():
                                shutil.rmtree(target)
                            else:
                                target.unlink()
                            summary['removed_caches'] += 1
                            summary['freed_bytes'] += size
                except (OSError, ValueError) as exc:
                    summary['errors'].append(f'{path.name}: {exc}')
            self._write(self.root / 'last_cleanup.json', dict(summary, checked_at=datetime.now(timezone.utc).isoformat()))
        return summary
