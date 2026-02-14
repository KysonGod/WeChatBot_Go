# WeChatBot Go + Python gRPC MVP（Windows wxauto）

这是一个最小可行方案（MVP）：
- Go 负责：调用 LLM（OpenAI 兼容 API）生成回复逻辑。
- Python 负责：通过 `wxauto` 操作 Windows 微信客户端，自动接收并发送消息。
- 两者通过 gRPC 通信（Go -> Python 发送回复；Go <- Python 轮询新消息）。

> 当前仅实现 **Windows 微信客户端（wxauto）** 路径。

## 重要说明：ChatGPT Pro 与 API

- 仅有 **ChatGPT Pro（网页订阅）**，通常**不能直接用于 API 调用**。
- 本项目需要“可编程 API”能力：`LLM_API_KEY + LLM_BASE_URL + LLM_MODEL`。
- 你可以使用：
  - OpenAI 官方 API；
  - 或任意兼容 OpenAI Chat Completions 的网关/服务。

## 自动收发能力（本次更新重点）

已支持自动链路：
1. Python bridge 使用 wxauto 监听 `Zachary`（可改 `WECHAT_TARGET`）新消息；
2. Go bot 轮询 bridge 获取新消息；
3. Go 调用 LLM 生成回复；
4. Go 再经 bridge 发送回复到微信。

默认 `BOT_MODE=auto`，无需手动在控制台输入消息。

## 目录结构

- `cmd/wechatbot/main.go`：MVP 主程序（Go），支持 `auto/manual` 模式
- `internal/llm/provider.go`：LLM provider 选择层（当前实现 `compatible_openai`）
- `internal/openai/client.go`：OpenAI 兼容接口调用
- `internal/bridge/client.go`：桥接调用层（Chat + Poll）
- `python/bridge_server.py`：gRPC 服务端（Python，包含 wxauto 监听/收发）
- `python/grpc_client.py`：Python gRPC 客户端 helper
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

## 最快启动（Windows PowerShell）

> 先把 `wxauto/` 放到仓库根目录，并填写好 `.env` 必填项。

```powershell
./scripts/quick_start_windows.ps1
```

该脚本会：
1. 加载 `.env` 到当前会话；
2. 新开 PowerShell 窗口启动 Python bridge；
3. 当前窗口启动 Go bot（默认 `BOT_MODE=auto`）。

## 使用步骤（Windows PowerShell）

### 1) 启动 Python bridge

```powershell
cd python
pip install -r requirements.txt
python bridge_server.py --host 127.0.0.1 --port 50051 --project-root ..
```

### 2) 启动 Go bot

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

默认 `BOT_MODE=auto` 会自动监听并回复，不需要手动输入。
如需手动输入测试，可设置：`BOT_MODE=manual`。

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
- wxauto 不同版本接口可能存在差异；本项目已按官方监听方式处理 `GetListenMessage()` 返回（键为 Chat 对象，需读取 `.who`），优先使用监听 API（`AddListenChat/GetListenMessage`），并包含 `GetAllMessage` 回退逻辑。


## 分支提示（关于 “no history in common with trunk”）

若你的代码平台提示 `Branch has no history in common with trunk`，说明当前仓库分支祖先与 trunk 不一致（通常是历史被重写或导入方式导致）。

建议：
1. 在代码平台上从 trunk 新建一个干净分支；
2. 将本项目改动以 patch/cherry-pick 方式应用到该分支；
3. 再发起 PR。

