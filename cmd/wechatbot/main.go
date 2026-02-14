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
	"wechatbot_mvp/internal/llm"
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

	llmProvider, err := llm.NewProvider(cfg.LLMProvider, cfg.LLMAPIKey, cfg.LLMBaseURL, cfg.LLMModel)
	if err != nil {
		fmt.Fprintf(os.Stderr, "LLM provider error: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("MVP bot started. target=%s, provider=%s, model=%s, mode=%s\n", cfg.TargetRemark, cfg.LLMProvider, cfg.LLMModel, cfg.BotMode)

	if strings.EqualFold(cfg.BotMode, "manual") {
		runManualMode(ctx, cfg, bridgeClient, llmProvider)
		return
	}
	runAutoMode(ctx, cfg, bridgeClient, llmProvider)
}

func runManualMode(ctx context.Context, cfg config.Config, bridgeClient *bridge.Client, llmProvider llm.Provider) {
	fmt.Println("手动模式：请输入来自 Zachary 的消息，输入 exit 退出。")
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
		handleAndReply(ctx, cfg, bridgeClient, llmProvider, input)
	}
	if err := scanner.Err(); err != nil {
		fmt.Fprintf(os.Stderr, "stdin error: %v\n", err)
	}
}

func runAutoMode(ctx context.Context, cfg config.Config, bridgeClient *bridge.Client, llmProvider llm.Provider) {
	fmt.Printf("自动模式已启动：每 %d 秒轮询 %s 新消息。\n", cfg.PollIntervalSeconds, cfg.TargetRemark)
	interval := time.Duration(cfg.PollIntervalSeconds) * time.Second

	for {
		pollCtx, cancel := context.WithTimeout(ctx, 30*time.Second)
		polled, err := bridgeClient.PollMessage(pollCtx, cfg.TargetRemark)
		cancel()
		if err != nil {
			fmt.Fprintf(os.Stderr, "Poll message failed: %v\n", err)
			time.Sleep(interval)
			continue
		}

		if !polled.HasNew || strings.TrimSpace(polled.Message) == "" {
			time.Sleep(interval)
			continue
		}

		fmt.Printf("Zachary> %s\n", polled.Message)
		handleAndReply(ctx, cfg, bridgeClient, llmProvider, polled.Message)
		time.Sleep(interval)
	}
}

func handleAndReply(ctx context.Context, cfg config.Config, bridgeClient *bridge.Client, llmProvider llm.Provider, input string) {
	replyCtx, cancel := context.WithTimeout(ctx, 90*time.Second)
	reply, err := llmProvider.Reply(replyCtx, cfg.SystemPrompt, input)
	cancel()
	if err != nil {
		fmt.Fprintf(os.Stderr, "LLM error: %v\n", err)
		return
	}
	fmt.Printf("Bot> %s\n", reply)

	if err := bridgeClient.SendToWX(ctx, cfg.TargetRemark, cfg.SystemPrompt, input, reply); err != nil {
		fmt.Fprintf(os.Stderr, "Send to WeChat failed: %v\n", err)
		return
	}
	fmt.Println("已通过 wxauto gRPC bridge 发送到微信。")
}
