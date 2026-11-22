@echo off
cd /d "%~dp0.."
uv run --project python --directory python python -m grpc_tools.protoc -I ../proto --python_out=pbuf --grpc_python_out=pbuf ../proto/streaming.proto