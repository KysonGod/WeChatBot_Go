package config

import (
	"fmt"
	"os"
)

type Config struct {
	OpenAIAPIKey  string
	OpenAIBaseURL string
	OpenAIModel   string
	TargetRemark  string
	BridgeAddr    string
	SystemPrompt  string
}

func Load() (Config, error) {
	cfg := Config{
		OpenAIAPIKey:  os.Getenv("OPENAI_API_KEY"),
		OpenAIBaseURL: getOrDefault("OPENAI_BASE_URL", "https://api.openai.com/v1"),
		OpenAIModel:   getOrDefault("OPENAI_MODEL", "gpt-5.2"),
		TargetRemark:  getOrDefault("WECHAT_TARGET", "Zachary"),
		BridgeAddr:    getOrDefault("PY_BRIDGE_ADDR", "127.0.0.1:50051"),
		SystemPrompt:  getOrDefault("BOT_SYSTEM_PROMPT", "你是一个温柔、善良、多智的女朋友风格助手。请用自然、关心、可靠的语气回复 Zachary。"),
	}

	if cfg.OpenAIAPIKey == "" {
		return cfg, fmt.Errorf("OPENAI_API_KEY is required")
	}
	return cfg, nil
}

func getOrDefault(key, fallback string) string {
	v := os.Getenv(key)
	if v == "" {
		return fallback
	}
	return v
}
