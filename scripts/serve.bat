@echo off
setlocal
cd /d "%~dp0.."
if "%2"=="" (echo Usage: serve ^<py^|bun^> ^<rest^|soap^|gql^|pbuf^> & exit /b 1)
call "%~dp0_env.bat" %1 %2
echo Starting %1 %2 on port %PORT%

if /i "%1"=="py" goto py
if /i "%1"=="bun" goto bun
echo Unknown runtime %1 & exit /b 1

:py
if /i "%2"=="pbuf" (
  uv run --project python --directory python python pbuf/server.py
) else if /i "%2"=="soap" (
  uv run --project python --directory python waitress-serve --port=%PORT% --threads=16 soap.main:app
) else (
  uv run --project python --directory python uvicorn %2.main:app --port %PORT%
)
exit /b

:bun
bun run node/%2/index.ts
exit /b