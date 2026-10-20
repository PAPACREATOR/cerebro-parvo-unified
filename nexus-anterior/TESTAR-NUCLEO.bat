@echo off
setlocal
cd /d "%~dp0"

echo === NEXUS LAB - TESTE DO NUCLEO ===
where git >nul 2>nul || (echo FAIL: Git nao encontrado.& exit /b 1)
for /f "delims=" %%i in ('git rev-parse HEAD') do set "SHA=%%i"
echo SHA: %SHA%
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File ".\nexus\windows\check-nexus.ps1" -Suite core
set "RC=%ERRORLEVEL%"

echo.
if "%RC%"=="0" (
  echo NEXUS-LAB NUCLEO = PASS
) else (
  echo NEXUS-LAB NUCLEO = FAIL
)
echo SHA TESTADO = %SHA%
exit /b %RC%
