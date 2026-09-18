@echo off
echo Starting Tinkoff Trading Bot...
if exist "venv\Scripts\python.exe" goto RUN

echo Virtual environment not found. Creating...
if exist "venv" rd /s /q venv
python -m venv venv
call venv\Scripts\activate.bat
pip install -r requirements.txt
goto STARTBOT

:RUN
call venv\Scripts\activate.bat

:STARTBOT
python -m app.main
pause
