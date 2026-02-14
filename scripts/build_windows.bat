@echo off
setlocal

if "%OPENAI_API_KEY%"=="" (
  echo [WARN] OPENAI_API_KEY is empty. Please set it before running the exe.
)

echo Building wechatbot_mvp.exe ...
set GOOS=windows
set GOARCH=amd64
go build -o build\wechatbot_mvp.exe .\cmd\wechatbot
if errorlevel 1 (
  echo Build failed.
  exit /b 1
)

echo Build success: build\wechatbot_mvp.exe
exit /b 0
