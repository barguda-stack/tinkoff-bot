@echo off
echo Updating code from GitHub...
git fetch origin
git reset --hard origin/master

echo Checking environment...
findstr /C:"/home/jules" "venv\pyvenv.cfg" >nul 2>&1
if %errorlevel% equ 0 (
    echo Found broken environment. Deleting...
    rd /s /q venv
)
echo Update complete! Press any key to exit.
pause > nul
