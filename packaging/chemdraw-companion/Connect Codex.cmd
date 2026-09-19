@echo off
setlocal
"%~dp0runtime\python.exe" -I -B "%~dp0connect_codex.py" %*
set "connect_exit=%errorlevel%"
echo.
echo Codex registration and a successful model tool call are separate checks.
pause
exit /b %connect_exit%
