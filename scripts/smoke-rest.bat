@echo off
setlocal
call "%~dp0_env.bat" %1 rest
echo --- GET /users/1 (expect 200)
curl.exe -s -i http://localhost:%PORT%/users/1 | findstr /b "HTTP"
echo --- GET /users/99999 (expect 404)
curl.exe -s -i http://localhost:%PORT%/users/99999 | findstr /b "HTTP"
echo --- POST /users (expect 201)
echo {"name":"smoke","age":30}> "%TEMP%\smoke.json"
curl.exe -s -i -X POST http://localhost:%PORT%/users -H "Content-Type: application/json" --data-binary "@%TEMP%\smoke.json" | findstr /b "HTTP"
echo --- POST /users invalid (expect 400)
echo {"name":"","age":30}> "%TEMP%\smoke.json"
curl.exe -s -i -X POST http://localhost:%PORT%/users -H "Content-Type: application/json" --data-binary "@%TEMP%\smoke.json" | findstr /b "HTTP"