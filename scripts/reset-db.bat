@echo off
cd /d "%~dp0.."
uv run --project python python db/init.py