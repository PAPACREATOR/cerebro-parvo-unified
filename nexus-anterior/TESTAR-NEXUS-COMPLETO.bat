@echo off
setlocal
cd /d "%~dp0"

echo === NEXUS LAB - TESTE COMPLETO ===
where git >nul 2>nul || (echo FAIL: Git nao encontrado.& exit /b 1)
for /f "delims=" %%i in ('git rev-parse HEAD') do set "SHA=%%i"
echo SHA: %SHA%
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File ".\nexus\windows\check-nexus.ps1" -Suite all
set "RC=%ERRORLEVEL%"

echo.
if "%RC%"=="0" (
  echo NEXUS-LAB COMPLETO = PASS
) else (
  echo NEXUS-LAB COMPLETO = FAIL
)
echo SHA TESTADO = %SHA%
exit /b %RC%
