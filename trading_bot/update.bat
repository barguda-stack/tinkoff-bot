@echo off
chcp 65001 > nul
echo Обновление Торгового Бота из GitHub...
git fetch origin
git reset --hard origin/master

echo Проверка виртуального окружения...
findstr /C:"/home/jules" "venv\pyvenv.cfg" >nul 2>&1
if %errorlevel% equ 0 (
    echo Найдено нерабочее окружение. Удаляю...
    rd /s /q venv
)

echo Обновление завершено! Перезапуск бота...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do taskkill /f /pid %%a >nul 2>&1

start "" run.bat
