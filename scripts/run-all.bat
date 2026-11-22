@echo off
rem Usage: scripts\run-all.bat [duration, default 60s]
setlocal
cd /d "%~dp0.."
set DUR=%1
if "%DUR%"=="" set DUR=60s
for /f %%T in ('powershell -nologo -command "Get-Date -Format yyyyMMdd-HHmm"') do set STAMP=%%T

for %%U in (50 200 500) do (
  for %%R in (py bun) do (
    for %%S in (rest soap gql pbuf) do call :run %%R %%S %%U
  )
)
echo.
echo All done. Next: uv run --project python python scripts\report.py
exit /b

:run
set RT=%1
set SVC=%2
set U=%3
set OUT=results\%STAMP%_%RT%_%SVC%_u%U%_t%DUR%
call "%~dp0_env.bat" %RT% %SVC%
set /a RATE=U/10
if %RATE% lss 1 set RATE=1
echo === %RT% %SVC% users=%U% port=%PORT%
call :kill
call "%~dp0reset-db.bat"
mkdir "%OUT%" 2>nul
start "bench-server" /min cmd /c ""%~dp0serve.bat" %RT% %SVC% > "%OUT%\server.log" 2>&1"
set TRIES=0
:wait
netstat -ano | findstr /R /C:":%PORT% .*LISTENING" >nul && goto ready
set /a TRIES+=1
if %TRIES% geq 60 (echo ERROR: server did not start, see %OUT%\server.log & call :kill & exit /b)
timeout /t 1 /nobreak >nul
goto wait
:ready
call "%~dp0loadtest.bat" %RT% %SVC% %U% %RATE% %DUR% "%OUT%"
call :kill
timeout /t 3 /nobreak >nul
exit /b

:kill
for /f "tokens=5" %%P in ('netstat -ano ^| findstr /R /C:":%PORT% .*LISTENING"') do taskkill /T /F /PID %%P >nul 2>&1
taskkill /T /F /FI "WINDOWTITLE eq bench-server*" >nul 2>&1
set KT=0
:freed
netstat -ano | findstr /R /C:":%PORT% .*LISTENING" >nul || exit /b
set /a KT+=1
if %KT% geq 15 exit /b
timeout /t 1 /nobreak >nul
goto freed