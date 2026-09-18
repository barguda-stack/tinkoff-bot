@echo off
echo Starting Tinkoff Trading Bot...
if not exist "venv\Scripts\activate.bat" (
    echo Virtual environment not found. Creating it...
    if exist "venv" rd /s /q venv
    python -m venv venv
    call venv\Scripts\activate.bat
    echo Installing requirements...
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)
python -m app.main
pause
