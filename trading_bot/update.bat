@echo off
echo Updating Tinkoff Trading Bot from GitHub...
git fetch origin
git reset --hard origin/master
echo Checking for broken virtual environments...
findstr /C:"/home/jules" "venv\pyvenv.cfg" >nul 2>&1
if %errorlevel% equ 0 (
    echo Found broken environment. Removing it...
    rd /s /q venv
)
echo Update complete!
pause
