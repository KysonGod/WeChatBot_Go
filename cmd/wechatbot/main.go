package main

import (
	"bufio"
	"context"
	"fmt"
	"os"
	"strings"
	"time"

	"wechatbot_mvp/internal/bridge"
	"wechatbot_mvp/internal/config"
	"wechatbot_mvp/internal/openai"
)

func main() {
	cfg, err := config.Load()
	if err != nil {
		fmt.Fprintf(os.Stderr, "config error: %v\n", err)
		os.Exit(1)
	}

	ctx := context.Background()
	bridgeClient, err := bridge.New(ctx, cfg.BridgeAddr)
	if err != nil {
		fmt.Fprintf(os.Stderr, "gRPC bridge connect failed: %v\n", err)
		os.Exit(1)
	}
	defer bridgeClient.Close()

	llm := openai.New(cfg.OpenAIAPIKey, cfg.OpenAIBaseURL, cfg.OpenAIModel)
	fmt.Printf("MVP bot started. target=%s, model=%s\n", cfg.TargetRemark, cfg.OpenAIModel)
	fmt.Println("请输入来自 Zachary 的消息，输入 exit 退出。")

	scanner := bufio.NewScanner(os.Stdin)
	for {
		fmt.Print("Zachary> ")
		if !scanner.Scan() {
			break
		}
		input := strings.TrimSpace(scanner.Text())
		if input == "" {
			continue
		}
		if strings.EqualFold(input, "exit") {
			break
		}

		replyCtx, cancel := context.WithTimeout(ctx, 90*time.Second)
		reply, err := llm.Reply(replyCtx, cfg.SystemPrompt, input)
		cancel()
		if err != nil {
			fmt.Fprintf(os.Stderr, "LLM error: %v\n", err)
			continue
		}
		fmt.Printf("Bot> %s\n", reply)

		if err := bridgeClient.SendToWX(ctx, cfg.TargetRemark, cfg.SystemPrompt, input, reply); err != nil {
			fmt.Fprintf(os.Stderr, "Send to WeChat failed: %v\n", err)
			continue
		}
		fmt.Println("已通过 wxauto gRPC bridge 发送到微信。")
	}

	if err := scanner.Err(); err != nil {
		fmt.Fprintf(os.Stderr, "stdin error: %v\n", err)
	}
}
