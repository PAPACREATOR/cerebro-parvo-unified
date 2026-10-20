@echo off
setlocal
cd /d "C:\Nexus"
set "PYTHONUTF8=1"
set "PATH=C:\Nexus\ferramentas\ffmpeg;%PATH%"
if /i "%~1"=="--arranque" goto modelos
"C:\Nexus\ambientes\host\Scripts\python.exe" -X utf8 "C:\Nexus\configuracao\testes-reais.py"
set "resultado=%errorlevel%"
echo.
echo Relatorio: C:\Nexus\registos\ultimo-teste-real.json
goto fim
:modelos
"C:\Nexus\ambientes\host\Scripts\python.exe" -X utf8 "C:\Nexus\configuracao\testar-arranque-modelos.py"
set "resultado=%errorlevel%"
echo.
echo Relatorio: C:\Nexus\registos\arranque-modelos-teste.json
:fim
if /i not "%~1"=="--automatico" if /i not "%~2"=="--automatico" pause
exit /b %resultado%
