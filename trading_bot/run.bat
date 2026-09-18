@echo off
echo Запуск бота...
if exist "venv\Scripts\python.exe" goto RUN

echo Виртуальное окружение не найдено. Создаю...
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
