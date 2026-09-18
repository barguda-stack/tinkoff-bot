@echo off
chcp 1251 > nul
echo Обновление кода из GitHub...
git fetch origin
git reset --hard origin/master

echo Проверка окружения...
findstr /C:"/home/jules" "venv\pyvenv.cfg" >nul 2>&1
if %errorlevel% equ 0 (
    echo Найдено нерабочее окружение. Удаляю...
    rd /s /q venv
)
echo Обновление завершено! Нажмите любую клавишу для выхода...
pause > nul
