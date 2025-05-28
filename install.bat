@echo off

cd /d "%~dp0"

echo Installing dependencies...

npm install
if errorlevel 1 (
  echo.
  echo [ERROR] npm install failed!
  pause
  exit /b 1
)

echo Building project...

npm run build
if errorlevel 1 (
  echo.
  echo [ERROR] npm run build failed!
  pause
  exit /b 1
)

pause