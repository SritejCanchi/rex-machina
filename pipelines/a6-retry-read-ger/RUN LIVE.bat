@echo off
setlocal
cd /d "%~dp0"
title Rex Machina - Assignment 6 live run
if "%ANTHROPIC_API_KEY%"=="" (
  echo   ANTHROPIC_API_KEY is not set in this window.
  echo   Use PowerShell instead:  $env:ANTHROPIC_API_KEY = "your-key"
  pause
  exit /b 1
)
set "PY="
call :try py
call :try python
call :tryexe "%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
call :tryexe "%LOCALAPPDATA%\Python\bin\python.exe"
call :tryexe "%USERPROFILE%\anaconda3\python.exe"
if not defined PY ( echo   No working Python found. & pause & exit /b 1 )
"%PY%" run_live.py
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
