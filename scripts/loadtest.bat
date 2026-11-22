@echo off
setlocal
cd /d "%~dp0.."
if "%2"=="" (echo Usage: loadtest ^<py^|bun^> ^<rest^|soap^|gql^|pbuf^> [users] [rate] [duration] [outdir] & exit /b 1)
call "%~dp0_env.bat" %1 %2

set USERS=%3
if "%USERS%"=="" set USERS=50
set RATE=%4
if "%RATE%"=="" set RATE=10
set DURATION=%5
if "%DURATION%"=="" set DURATION=60s
set OUT=%6
if "%OUT%"=="" (
  for /f %%T in ('powershell -nologo -command "Get-Date -Format yyyyMMdd-HHmm"') do set STAMP=%%T
  set OUT=results\%STAMP%_%1_%2_u%USERS%_t%DURATION%
)
if not exist "%OUT%" mkdir "%OUT%"

(echo runtime=%1& echo service=%2& echo port=%PORT%& echo users=%USERS%& echo rate=%RATE%& echo duration=%DURATION%) > "%OUT%\params.txt"

echo Running locust: users=%USERS% rate=%RATE% duration=%DURATION% -^> %OUT%
uv run --project python locust -f loadtest/locustfile_%2.py ^
  --host http://localhost:%PORT% --headless --reset-stats --only-summary ^
  -u %USERS% -r %RATE% -t %DURATION% ^
  --csv "%OUT%\locust" --logfile "%OUT%\locust.log"