@echo off
chcp 1251 > nul
echo Starting Tinkoff Trading Bot...
set VENV_OK=0
if exist "venv\Scripts\activate.bat" (
    set VENV_OK=1
)
if "%VENV_OK%"=="0" (
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
