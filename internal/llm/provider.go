package llm

import (
	"context"
	"fmt"
	"strings"

	"wechatbot_mvp/internal/openai"
)

type Provider interface {
	Reply(ctx context.Context, systemPrompt, userMsg string) (string, error)
}

func NewProvider(providerName, apiKey, baseURL, model string) (Provider, error) {
	switch strings.ToLower(strings.TrimSpace(providerName)) {
	case "openai", "compatible_openai", "openai_compatible", "compat":
		return openai.New(apiKey, baseURL, model), nil
	default:
		return nil, fmt.Errorf("unsupported LLM_PROVIDER=%q (supported: compatible_openai/openai)", providerName)
	}
}
