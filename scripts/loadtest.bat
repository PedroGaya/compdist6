@echo off
setlocal
cd /d "%~dp0.."
if "%2"=="" (echo Usage: loadtest ^<py^|bun^> ^<rest^|soap^|graphql^|grpc^> [users] [rate] [time] & exit /b 1)
call "%~dp0_env.bat" %1 %2

set USERS=%3
if "%USERS%"=="" set USERS=50
set RATE=%4
if "%RATE%"=="" set RATE=10
set TIME=%5
if "%TIME%"=="" set TIME=60s

uv run --project python locust -f loadtest/locustfile_%2.py ^
  --host http://localhost:%PORT% --headless ^
  -u %USERS% -r %RATE% -t %TIME% ^
  --csv loadtest/results/%1_%2_u%USERS%