@echo off
REM Library repository update script for Windows
REM Usage: update_library.bat

echo === Utayomi Library Update Script ===

set LIBRARY_DIR=.\input\library

if not exist "%LIBRARY_DIR%" (
    echo Error: Library directory not found: %LIBRARY_DIR%
    pause
    exit /b 1
)

cd "%LIBRARY_DIR%"

if not exist ".git" (
    echo Error: Not a git repository: %LIBRARY_DIR%
    pause
    exit /b 1
)

echo Current directory: %CD%
git remote get-url origin

REM Check for local changes
git status --porcelain > temp_status.txt
for /f %%i in ("temp_status.txt") do set size=%%~zi
del temp_status.txt

if %size% gtr 0 (
    echo Warning: Local changes detected.
    git status --short
    
    set /p choice="Do you want to discard local changes and update? (y/N): "
    if /i "%choice%"=="y" (
        echo Discarding local changes...
        git restore .
        git clean -fd
    ) else (
        echo Update cancelled. Please handle local changes manually.
        pause
        exit /b 1
    )
)

echo Fetching latest changes...
git fetch origin

echo Updating to latest version...
git pull origin main

if %errorlevel% equ 0 (
    echo ✅ Library updated successfully!
    echo Latest commit:
    git log -1 --oneline
) else (
    echo ❌ Update failed. Please check the error messages above.
    pause
    exit /b 1
)

echo === Update completed ===
pause