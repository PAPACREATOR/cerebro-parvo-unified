@echo off
setlocal
python "%~dp0test_web_research_wiki_100k.py" --cases 100000 --output "%~dp0results"
exit /b %ERRORLEVEL%
