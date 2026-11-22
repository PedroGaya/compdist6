@echo off
setlocal
cd /d "%~dp0.."
if "%2"=="" (echo Usage: serve ^<py^|bun^> ^<rest^|soap^|graphql^|grpc^> & exit /b 1)
call "%~dp0_env.bat" %1 %2
echo Starting %1 %2 on port %PORT%

if /i "%1"=="py" (
  if /i "%2"=="grpc" (
    uv run --project python --directory python python grpc/server.py
  ) else if /i "%2"=="soap" (
    uv run --project python --directory python waitress-serve --port=%PORT% --threads=16 soap.main:app
  ) else (
    uv run --project python --directory python uvicorn %2.main:app --port %PORT%
  )
)