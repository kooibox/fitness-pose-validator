@echo off
echo ========================================
echo Fitness Pose Validator - Build Script
echo ========================================
echo.

REM Activate virtual environment
echo [1/4] Activating virtual environment...
call venv\Scripts\activate.bat

REM Check PyInstaller
echo [2/4] Checking PyInstaller...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

REM Clean old build files
echo [3/4] Cleaning old build files...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist

REM Build
echo [4/4] Building executable...
echo This may take 5-10 minutes, please wait...
echo.

pyinstaller --onefile --windowed ^
    --name "FitnessPoseValidator" ^
    --add-data "models;models" ^
    --add-data "gui/resources;gui/resources" ^
    --hidden-import "PyQt6" ^
    --hidden-import "PyQt6.QtCore" ^
    --hidden-import "PyQt6.QtGui" ^
    --hidden-import "PyQt6.QtWidgets" ^
    --hidden-import "cv2" ^
    --hidden-import "mediapipe" ^
    --hidden-import "numpy" ^
    --hidden-import "matplotlib" ^
    --hidden-import "PIL" ^
    --hidden-import "PIL.Image" ^
    --hidden-import "PIL.ImageDraw" ^
    --hidden-import "PIL.ImageFont" ^
    run_gui.py

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build Complete!
echo ========================================
echo.
echo Output: dist\FitnessPoseValidator.exe
echo.
for %%A in (dist\FitnessPoseValidator.exe) do echo File size: %%~zA bytes
echo.
echo Press any key to exit...
pause >nul
