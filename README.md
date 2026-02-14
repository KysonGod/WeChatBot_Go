# WeChatBot Go + Python gRPC MVP（Windows wxauto）

这是一个最小可行方案（MVP）：
- Go 负责：读取输入消息、调用 LLM（OpenAI 兼容 API）生成回复、通过 gRPC 发送给 Python。
- Python 负责：通过 `wxauto` 操作 Windows 微信客户端，把回复发给备注为 `Zachary` 的联系人。

> 当前仅实现 **Windows 微信客户端（wxauto）** 路径。

## 重要说明：ChatGPT Pro 与 API

- 仅有 **ChatGPT Pro（网页订阅）**，通常**不能直接用于 API 调用**。
- 本项目需要“可编程 API”能力：`LLM_API_KEY + LLM_BASE_URL + LLM_MODEL`。
- 你可以使用：
  - OpenAI 官方 API；
  - 或任意兼容 OpenAI Chat Completions 的网关/服务。

## 目录结构

- `cmd/wechatbot/main.go`：MVP 主程序（Go）
- `internal/llm/provider.go`：LLM provider 选择层（当前实现 `compatible_openai`）
- `internal/openai/client.go`：OpenAI 兼容接口调用
- `internal/bridge/client.go`：gRPC 客户端（Go -> Python）
- `python/bridge_server.py`：gRPC 服务端（Python）
- `python/requirements.txt`：Python 依赖
- `.env.example`：环境变量模板（包含必填项）
- `scripts/build_windows.bat`：Windows 构建脚本（生成 `build/wechatbot_mvp.exe`）

## 你需要准备的内容（必填）

1. `LLM_API_KEY`（必填）
2. `LLM_MODEL`（必填，填写你的 API 服务可用模型名）
3. `LLM_BASE_URL`（必填，兼容 OpenAI 的地址）
4. 在仓库根目录放入 `wxauto/` 源码（你会复制）
   - 参考地址：<https://github.com/cluic/wxauto.git>
   - 使用 `WeChat3.9.8` 或 `WeChat3.9.11` 分支
5. Windows 端安装并登录微信客户端（与 wxauto 匹配）

## 使用步骤

### 1) Python bridge（Windows）

```bash
cd python
pip install -r requirements.txt
python bridge_server.py --host 127.0.0.1 --port 50051 --project-root ..
```

### 2) Go bot（Windows PowerShell）

```powershell
# 在仓库根目录
Copy-Item .env.example .env
# 按需填写 .env 中的必填项

# 加载 .env 到当前 PowerShell 会话
Get-Content .env | ForEach-Object {
  if ($_ -match '^\s*#' -or $_ -match '^\s*$') { return }
  $k, $v = $_ -split '=', 2
  [Environment]::SetEnvironmentVariable($k, $v, 'Process')
}

go run .\cmd\wechatbot
```

程序启动后，在命令行输入来自 `Zachary` 的消息，bot 会：
1. 调用 LLM 生成“温柔、善良、多智的女朋友”风格回复；
2. 经 gRPC 交给 Python；
3. Python 使用 wxauto 将回复发给微信备注 `Zachary`。

## Windows 可执行文件（本地构建）

由于部分代码托管平台/PR 流程不支持直接提交二进制文件，本仓库不再跟踪 `*.exe`。

请在 Windows 上执行：

```bat
scripts\build_windows.bat
```

生成文件：`build/wechatbot_mvp.exe`

然后运行该 exe（确保 Python bridge 已启动，且环境变量已配置）。

## 说明

- 若 `wxauto` 未就绪，Python bridge 会进入 dry-run 模式，仅打印日志，不会真实发消息。
- 已支持 provider 抽象入口，当前默认 provider 为 `compatible_openai`，后续可继续扩展更多后端。
