@echo off
chcp 65001 > nul
echo Запуск Торгового Бота Tinkoff...
set VENV_OK=0
if exist "venv\Scripts\activate.bat" (
    set VENV_OK=1
)
if "%VENV_OK%"=="0" (
    echo Виртуальное окружение не найдено. Создаю (это займет пару минут)...
    if exist "venv" rd /s /q venv
    python -m venv venv
    call venv\Scripts\activate.bat
    echo Установка библиотек...
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)
python -m app.main
pause
