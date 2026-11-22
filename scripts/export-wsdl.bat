@echo off
cd /d "%~dp0.."
curl.exe -s "http://localhost:8002/?wsdl" -o schemas/streaming.wsdl
echo Saved schemas\streaming.wsdl