@echo off
echo Starting Tinkoff Trading Bot...
if not exist "venv\Scripts\activate.bat" (
    echo Please run python -m venv venv and pip install -r requirements.txt first.
)
call venv\Scripts\activate.bat
python -m app.main
pause
