set USERS=%3
if "%USERS%"=="" set USERS=50
set RATE=%4
if "%RATE%"=="" set RATE=10
set DURATION=%5
if "%DURATION%"=="" set DURATION=60s

echo Running locust: users=%USERS% rate=%RATE% duration=%DURATION%
uv run --project python locust -f loadtest/locustfile_%2.py ^
  --host http://localhost:%PORT% --headless --reset-stats --only-summary ^
  -u %USERS% -r %RATE% -t %DURATION% ^
  --csv loadtest/results/%1_%2_u%USERS%