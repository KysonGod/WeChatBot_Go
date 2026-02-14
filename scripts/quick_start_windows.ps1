Param(
  [string]$PythonExe = "python",
  [string]$BridgeHost = "127.0.0.1",
  [int]$BridgePort = 50051
)

$ErrorActionPreference = "Stop"

if (!(Test-Path ".env")) {
  Copy-Item .env.example .env
  Write-Host "[INFO] 已创建 .env，请先填写必填项（LLM_API_KEY/LLM_MODEL/LLM_BASE_URL）后重试。" -ForegroundColor Yellow
  exit 1
}

Get-Content .env | ForEach-Object {
  if ($_ -match '^\s*#' -or $_ -match '^\s*$') { return }
  $k, $v = $_ -split '=', 2
  [Environment]::SetEnvironmentVariable($k, $v, 'Process')
}

Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD/python'; $PythonExe bridge_server.py --host $BridgeHost --port $BridgePort --project-root .."

Start-Sleep -Seconds 2

go run .\cmd\wechatbot
