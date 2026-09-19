@echo off
setlocal
"%~dp0runtime\python.exe" -I -B "%~dp0install.py" %*
set "install_exit=%errorlevel%"
echo.
echo File installation does not connect an agent. Use Connect Codex.cmd separately.
pause
exit /b %install_exit%
