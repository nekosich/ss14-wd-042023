@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "PY_SCRIPT=%SCRIPT_DIR%fix-local-db.py"

if not exist "%PY_SCRIPT%" (
    echo [ERROR] File not found: "%PY_SCRIPT%"
    exit /b 1
)

where python >nul 2>nul
if "%ERRORLEVEL%"=="0" (
    python "%PY_SCRIPT%" %*
    set "EXIT_CODE=%ERRORLEVEL%"
    goto :done
)

where py >nul 2>nul
if "%ERRORLEVEL%"=="0" (
    py -3 "%PY_SCRIPT%" %*
    set "EXIT_CODE=%ERRORLEVEL%"
    goto :done
)

echo [ERROR] Python launcher not found. Install Python and ensure python.exe or py.exe is in PATH.
exit /b 1

:done
if not "%EXIT_CODE%"=="0" (
    echo [ERROR] DB fix failed with exit code %EXIT_CODE%.
    exit /b %EXIT_CODE%
)

echo [OK] DB fix completed.
exit /b 0
