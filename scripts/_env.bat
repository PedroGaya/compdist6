@echo off
rem Usage: call _env.bat <py|bun> <rest|soap|gql|pbuf>
set BASE=8000
if /i "%1"=="bun" set BASE=8010
set IDX=0
if /i "%2"=="rest" set IDX=1
if /i "%2"=="soap" set IDX=2
if /i "%2"=="gql" set IDX=3
if /i "%2"=="pbuf" set IDX=4
set /a PORT=BASE+IDX