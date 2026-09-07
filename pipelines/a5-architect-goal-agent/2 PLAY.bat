@echo off
setlocal
cd /d "%~dp0"
title Rex Machina - Act 3
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
  echo   No working Python found. Run "1 VERIFY.bat" first for the details.
  pause
  exit /b 1
)
"%PY%" game\play.py
echo.
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
