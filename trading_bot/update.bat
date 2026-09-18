@echo off
chcp 1251 > nul
echo Updating Tinkoff Trading Bot from GitHub...
git fetch origin
git reset --hard origin/master

echo Checking for broken virtual environments...
findstr /C:"/home/jules" "venv\pyvenv.cfg" >nul 2>&1
if %errorlevel% equ 0 (
    echo Found broken environment. Removing it...
    rd /s /q venv
)

echo Update complete! Restarting bot...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do taskkill /f /pid %%a >nul 2>&1

start "" run.bat
