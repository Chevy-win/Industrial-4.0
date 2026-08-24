@echo off
setlocal

set "BUNDLE_DIR=%~dp0"

python -c "import struct,sys; assert sys.version_info[:2] == (3,12), 'Python 3.12 is required'; assert struct.calcsize('P') * 8 == 64, '64-bit Python is required'; print('Using:', sys.executable, sys.version)"
if errorlevel 1 goto :environment_error

python -m pip install --no-index --find-links "%BUNDLE_DIR%" ortools==9.15.6755
if errorlevel 1 goto :install_error

python -c "import ortools; from ortools.sat.python import cp_model; print('OR-Tools installed:', ortools.__version__); print('CP-SAT import: OK')"
if errorlevel 1 goto :install_error

echo.
echo Offline installation completed successfully.
exit /b 0

:environment_error
echo.
echo ERROR: Activate a 64-bit Python 3.12 environment, then run this file again.
exit /b 1

:install_error
echo.
echo ERROR: Offline installation or verification failed.
exit /b 1
