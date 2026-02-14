package config

import (
	"fmt"
	"os"
)

type Config struct {
	LLMProvider string
	LLMAPIKey   string
	LLMBaseURL  string
	LLMModel    string

	TargetRemark string
	BridgeAddr   string
	SystemPrompt string
}

func Load() (Config, error) {
	cfg := Config{
		LLMProvider: getOrDefault("LLM_PROVIDER", "compatible_openai"),
		LLMAPIKey:   getOrDefault("LLM_API_KEY", os.Getenv("OPENAI_API_KEY")),
		LLMBaseURL:  getOrDefault("LLM_BASE_URL", getOrDefault("OPENAI_BASE_URL", "https://api.openai.com/v1")),
		LLMModel:    getOrDefault("LLM_MODEL", getOrDefault("OPENAI_MODEL", "gpt-5.2")),

		TargetRemark: getOrDefault("WECHAT_TARGET", "Zachary"),
		BridgeAddr:   getOrDefault("PY_BRIDGE_ADDR", "127.0.0.1:50051"),
		SystemPrompt: getOrDefault("BOT_SYSTEM_PROMPT", "你是一个温柔、善良、多智的女朋友风格助手。请用自然、关心、可靠的语气回复 Zachary。"),
	}

	if cfg.LLMAPIKey == "" {
		return cfg, fmt.Errorf("LLM_API_KEY is required (or set OPENAI_API_KEY for backward compatibility)")
	}
	if cfg.LLMModel == "" {
		return cfg, fmt.Errorf("LLM_MODEL is required")
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
