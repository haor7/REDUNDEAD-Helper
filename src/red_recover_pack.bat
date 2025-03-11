@echo off
echo REDundead Helper Packaging Script
echo =========================

echo 1. Check Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [Error] No Python installation detected! Please install Python 3.7 or higher first.
    goto :error
)
echo [Success] Python installation detected.

echo 2. Install required libraries...
echo Installing PyQt5...
pip install PyQt5
echo Installing pywin32...
pip install pywin32
echo Installing PyInstaller...
pip install pyinstaller
echo [Success] Installation of dependent libraries completed.

echo 3. Create source code file...
copy src\redundead_gui.py src\redundead_gui_temp.py >nul 2>&1
echo [Success] Source code file is ready.

echo 4. Wait 5 seconds to ensure installation is complete...
timeout /t 5 /nobreak

echo 5. Start packaging program...
echo Use python -m PyInstaller command to package...
python -m PyInstaller --onefile --windowed --uac-admin --name="RED_helper" src\redundead_gui_temp.py
if %errorlevel% neq 0 (
    echo [Warning] Failed to use python -m PyInstaller command, try to use PyInstaller directly...
    PyInstaller --onefile --windowed --uac-admin --name="RERED_helper" src\redundead_gui_temp.py
    if %errorlevel% neq 0 (
        echo [Error] Packaging failed! Please check whether PyInstaller is installed correctly.
        goto :error
    )
)
echo [Success] Packaging is complete.

echo 6. Clean up temporary files...
del src\redundead_gui_temp.py >nul 2>&1
rmdir /s /q __pycache__ >nul 2>&1
rmdir /s /q build >nul 2>&1
del "RED_helper.spec" >nul 2>&1
echo [Success] Clean up completed.

echo.
echo ================================================
echo Packaging is successful! The executable file is located in the dist folder
echo 文件名: REDundead_helper.exe
echo.
echo Instructions for use:
echo 1. Right-click "RED_helper.exe"
echo 2. Select "Run as Administrator"
echo 3. Follow the prompts on the interface
echo ================================================
echo.
pause
goto :eof

:error
echo.
echo [Abort] The packaging process was terminated due to the above error.
echo.
echo You can try to manually enter the following command to install and run PyInstaller:
echo.
echo pip install pyinstaller
echo python -m PyInstaller --onefile --windowed --uac-admin --name="REDundead_helper" redundead_gui.py
echo.
pause
exit /b 1