@echo off
title Email Crunch Launcher
setlocal

:: 1. Check Python in LocalAppData first (prevents Windows Store alias trap)
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" "%~dp0main.py"
    goto end
)

:: 2. Check general Python installations
for %%P in (
    "%ProgramFiles%\Python311\python.exe"
    "%ProgramFiles%\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
) do (
    if exist "%%~P" (
        "%%~P" "%~dp0main.py"
        goto end
    )
)

:: 3. Fallback to py launcher or PATH python
python "%~dp0main.py" 2>nul
if %errorlevel% equ 0 goto end

echo =======================================================
echo Python was not found!
echo Please run: winget install Python.Python.3.11
echo =======================================================
pause

:end
endlocal
