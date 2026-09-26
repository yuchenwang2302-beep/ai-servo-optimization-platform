# SPDX-FileCopyrightText: 2025-2026 Yuchen Wang
# SPDX-License-Identifier: GPL-3.0-only
"""Read-only startup diagnostics; never start MATLAB or check out a license."""
import argparse
from datetime import datetime
import importlib
import importlib.metadata as metadata
import json
from pathlib import Path
import re
import site
import struct
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
MODULES = {
    'PyQt5': 'PyQt5.QtWidgets', 'PyQt5-Qt5': 'PyQt5', 'PyQt5-sip': 'PyQt5.sip',
    'numpy': 'numpy', 'scipy': 'scipy', 'matplotlib': 'matplotlib',
    'contourpy': 'contourpy', 'cycler': 'cycler', 'fonttools': 'fontTools',
    'kiwisolver': 'kiwisolver', 'packaging': 'packaging', 'pillow': 'PIL',
    'pyparsing': 'pyparsing', 'python-dateutil': 'dateutil', 'six': 'six',
    'matlabengine': 'matlab.engine',
}
MODELS = (
    'identification/Spd_Discrete.slx', 'identification/Spd_Discrete2.slx',
    'optimization/single_objective/Jerk_FF_Step_2023.slx',
    'optimization/multi_objectives/Jerk_FF_Step_2023_2.slx',
)


def inside(path, directory):
    return Path(path).resolve().is_relative_to(Path(directory).resolve())


def pins(path):
    return {name.lower(): version for name, version in
            re.findall(r'^([\w.-]+)==([^\s\\]+)', path.read_text(encoding='utf-8'), re.M)}


def collect_report(environment=None):
    environment = Path(environment or ROOT / '.venv').resolve()
    expected = json.loads((ROOT / 'tools/bootstrap.json').read_text(encoding='utf-8'))
    errors = []
    report = {
        'generated_at': datetime.now().astimezone().isoformat(),
        'python': sys.version, 'executable': sys.executable, 'environment': sys.prefix,
        'base_python': sys.base_prefix, 'expected_environment': str(environment),
        'user_site_enabled': site.ENABLE_USER_SITE, 'dependencies': {}, 'errors': errors,
        'license_status': 'Not checked; verified only when starting a real MATLAB calculation.',
    }
    if Path(sys.prefix).resolve() != environment or not inside(sys.executable, environment):
        errors.append('Use this project\'s .venv interpreter via start_ui.bat; system Python is unsupported.')
    if '.'.join(map(str, sys.version_info[:3])) != expected['python_version']:
        errors.append('Python version differs from bootstrap.json; rebuild the project environment.')
    if Path(sys.base_prefix).resolve() != (ROOT / '.python' / expected['python_key']).resolve():
        errors.append('The base Python must be the pinned project-local runtime.')
    if sys.platform != 'win32' or struct.calcsize('P') != 8:
        errors.append('This environment lock requires 64-bit Windows and 64-bit Python.')
    config = Path(sys.prefix) / 'pyvenv.cfg'
    report['venv_config'] = config.read_text(encoding='utf-8') if config.is_file() else ''
    if not re.search(r'^include-system-site-packages\s*=\s*false\s*$', report['venv_config'], re.M | re.I):
        errors.append('Virtual environment isolation is disabled or missing.')
    if site.ENABLE_USER_SITE:
        errors.append('User site-packages must be disabled.')
    external_sites = [str(p) for p in sys.path if p and 'site-packages' in Path(p).parts
                      and not inside(p, environment)]
    report['external_site_packages'] = external_sites
    if external_sites:
        errors.append('External site-packages are present in the import path.')
    wanted = pins(ROOT / 'requirements.lock')
    if wanted != pins(ROOT / 'requirements.txt'):
        errors.append('requirements.txt and requirements.lock disagree; regenerate and validate the lock.')
    for name, target_version in wanted.items():
        entry = {'expected_version': target_version}
        try:
            distribution = metadata.distribution(name)
            entry['version'] = distribution.version
            entry['distribution_path'] = str(Path(distribution.locate_file('')).resolve())
            if distribution.version != target_version or not inside(entry['distribution_path'], environment):
                raise RuntimeError('Wrong version or a package outside this virtual environment.')
            module_name = next(value for key, value in MODULES.items() if key.lower() == name.lower())
            module = importlib.import_module(module_name)
            module_path = Path(module.__file__).resolve()
            entry['module_path'] = str(module_path)
            if not inside(module_path, environment):
                raise RuntimeError('Module was imported from outside this virtual environment.')
        except Exception as exc:
            entry['error'] = f'{type(exc).__name__}: {exc}'
            errors.append(f'{name}: {entry["error"]}')
        report['dependencies'][name] = entry
    try:
        engine = report['dependencies']['matlabengine']
        if 'error' in engine:
            raise RuntimeError('MATLAB Engine could not be imported.')
        arch_path = Path(engine['module_path']).with_name('_arch.txt')
        arch, binary, engine_binary, extern = arch_path.read_text().splitlines()[:4]
        matlab_root = Path(binary).resolve().parents[1]
        release = ET.parse(matlab_root / 'VersionInfo.xml').getroot().findtext('release')
        report['matlab'] = {'root': str(matlab_root), 'release': release, 'architecture': arch,
                            'native_library_directories': [binary, engine_binary, extern]}
        if release != expected['matlab_release'] or arch != 'win64':
            raise RuntimeError('Engine must reference a 64-bit MATLAB R2024b installation.')
        required = ['bin/win64/MATLAB.exe', 'toolbox/simulink',
                    'toolbox/mcb/utils/mcb_updateInverterParameters.m']
        missing = [p for p in required if not (matlab_root / p).exists()]
        if missing:
            raise RuntimeError('Missing MATLAB components: ' + ', '.join(missing))
    except Exception as exc:
        errors.append(f'MATLAB: {type(exc).__name__}: {exc}')
    report['matlab_models'] = list(MODELS)
    for model in MODELS:
        if not (ROOT / 'matlab_scripts' / model).is_file():
            errors.append('Missing Simulink model: ' + model)
    report['passed'] = not errors
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--environment', type=Path, help='Expected environment for rebuild verification.')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = collect_report(args.environment)
    serialized = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding='utf-8')
    print(serialized)
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
