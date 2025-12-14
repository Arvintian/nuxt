@echo off
setlocal enabledelayedexpansion

if "%1"=="clean" goto clean
if "%1"=="build" goto build
if "%1"=="install" goto install

echo Usage: %0 [clean^|build^|install]
exit /b 1

:clean
echo Cleaning build files...
if exist dist rmdir /s /q dist
for /d %%d in (*.egg-info) do rmdir /s /q "%%d" 2>nul
echo Clean complete
goto end

:build
call :clean
echo Building package...
python -m build -n --sdist
if errorlevel 1 (
    echo Build failed
    exit /b 1
)
echo Build complete
goto end

:install
call :build
echo Installing package...
pip uninstall -y nuxt
:: Find the latest package in dist folder
for %%f in (dist\nuxt*.whl dist\nuxt*.tar.gz) do set "latest_package=%%f"
if "!latest_package!"=="" (
    echo No package found in dist folder
    exit /b 1
)
echo Installing: !latest_package!
pip install "!latest_package!"
if errorlevel 1 (
    echo Install failed
    exit /b 1
)
echo Install complete
goto end

:end
endlocal
