# SPDX-FileCopyrightText: 2025-2026 Yuchen Wang
# SPDX-License-Identifier: GPL-3.0-only
param([string]$EnvironmentDirectory = '.venv')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$config = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'bootstrap.json') -Raw | ConvertFrom-Json
$environment = [IO.Path]::GetFullPath((Join-Path $projectRoot $EnvironmentDirectory))
if (-not $environment.StartsWith($projectRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'The environment must be inside this project.'
}
$python = Join-Path $environment 'Scripts\python.exe'
if (Test-Path -LiteralPath $environment) {
    if (Test-Path -LiteralPath $python) {
        & $python -I (Join-Path $PSScriptRoot 'check_environment.py') --environment $environment
        if ($LASTEXITCODE -eq 0) { Write-Host 'Existing environment is valid; nothing changed.'; exit 0 }
    }
    throw 'An environment already exists here. Preserve it outside the project before rebuilding; it will not be overwritten.'
}
# The Engine installer discovers MATLAB via this registry key on Windows.
$matlab = Get-ItemProperty -LiteralPath 'HKLM:\SOFTWARE\MathWorks\MATLAB\24.2' -ErrorAction Stop
if (-not (Test-Path -LiteralPath (Join-Path $matlab.MATLABROOT 'bin\win64\MATLAB.exe'))) {
    throw 'Install MATLAB R2024b (64-bit), Simulink and Motor Control Blockset first.'
}
$toolDirectory = Join-Path $projectRoot ('.tools\uv-' + $config.uv_version)
$archive = $toolDirectory + '.zip'
New-Item -ItemType Directory -Force -Path $toolDirectory | Out-Null
if (-not (Test-Path -LiteralPath $archive)) {
    Invoke-WebRequest -Uri $config.uv_url -OutFile $archive -UseBasicParsing
}
if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $config.uv_sha256) {
    throw 'uv download checksum mismatch. Preserve the downloaded archive for diagnosis and retry with a fresh download.'
}
Expand-Archive -LiteralPath $archive -DestinationPath $toolDirectory -Force
$uv = Join-Path $toolDirectory 'uv.exe'
# Process-local settings: no system PATH, Python registry or global packages are changed.
$env:UV_PYTHON_INSTALL_DIR = Join-Path $projectRoot '.python'
$env:UV_PYTHON_CPYTHON_BUILD = $config.python_build
$env:UV_CACHE_DIR = Join-Path $projectRoot '.tools\cache'
& $uv --no-config python install $config.python_version --no-bin --no-registry
if ($LASTEXITCODE -ne 0) { throw 'Python installation failed.' }
$basePython = Join-Path $env:UV_PYTHON_INSTALL_DIR ($config.python_key + '\python.exe')
& $uv --no-config venv --python $basePython $environment
if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed.' }
& $uv --no-config pip install --python $python --default-index https://pypi.org/simple --require-hashes --no-deps -r (Join-Path $projectRoot 'requirements-build.lock')
if ($LASTEXITCODE -ne 0) { throw 'Build-tool installation failed.' }
# Engine wheels contain the local MATLAB location. Always build afresh on this machine.
& $uv --no-config --no-cache pip install --python $python --default-index https://pypi.org/simple --require-hashes --no-deps --no-build-isolation -r (Join-Path $projectRoot 'requirements.lock')
if ($LASTEXITCODE -ne 0) { throw 'Runtime installation failed. The prior environment has not been modified.' }
& $python -I -m pip check
if ($LASTEXITCODE -ne 0) { throw 'Dependency compatibility check failed.' }
& $python -I (Join-Path $PSScriptRoot 'check_environment.py') --environment $environment
if ($LASTEXITCODE -ne 0) { throw 'Environment verification failed; inspect the report above.' }
Write-Host 'Environment ready. Use start_ui.bat. MATLAB licensing is verified during real calculation.'
