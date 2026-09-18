@echo off
echo Starting Tinkoff Trading Bot...

rem We must remove the broken virtual environment from Linux/Jules.
echo Checking for broken Linux environment...
findstr /C:"/home/jules" "venv\pyvenv.cfg" >nul 2>&1
if %errorlevel% equ 0 (
    echo Found broken environment. Deleting...
    rd /s /q venv
)

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
