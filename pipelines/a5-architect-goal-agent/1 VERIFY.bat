@echo off
setlocal
cd /d "%~dp0"
title Rex Machina - Assignment 5 - verify
echo.
echo ================================================================
echo   Rex Machina - Assignment 5 - The Architect
echo   Verification run.
echo ================================================================
echo.
set "PY="
call :try py
call :try python
call :tryexe "%LOCALAPPDATA%\Python\bin\python.exe"
call :tryexe "%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
call :tryexe "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
call :tryexe "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
call :tryexe "%USERPROFILE%\anaconda3\python.exe"
call :tryexe "%LOCALAPPDATA%\anaconda3\python.exe"
call :tryexe "%PROGRAMDATA%\anaconda3\python.exe"
if not defined PY (
  echo   No working Python found. Open a NEW terminal and try again,
  echo   or run this from an Anaconda Prompt.
  pause
  exit /b 1
)
echo   Interpreter: %PY%
"%PY%" -V
echo.
echo ---------------- test suite ----------------
"%PY%" tests\test_architect.py
echo.
echo ---------------- scripted playthroughs ----------------
"%PY%" tests\smoke.py
echo.
echo ---------------- agent reasoning, dry run ----------------
"%PY%" architect\architect.py --dry-run
echo.
echo   Done. Look for "35 passed, 0 failed" and "winnability: OK".
pause
exit /b 0
:try
if defined PY goto :eof
%1 -c "import sys" >nul 2>&1
if errorlevel 1 goto :eof
set "PY=%1"
goto :eof
:tryexe
if defined PY goto :eof
if not exist %1 goto :eof
%1 -c "import sys" >nul 2>&1
if errorlevel 1 goto :eof
set "PY=%~1"
goto :eof
