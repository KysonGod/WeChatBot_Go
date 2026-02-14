package bridge

import (
	"context"
	"encoding/json"
	"fmt"
	"os/exec"
)

type Client struct {
	addr string
}

type PollResult struct {
	HasNew  bool
	Message string
}

func New(_ context.Context, addr string) (*Client, error) {
	return &Client{addr: addr}, nil
}

func (c *Client) Close() error { return nil }

func (c *Client) SendToWX(ctx context.Context, targetRemark, persona, userMsg, reply string) error {
	_, err := c.call(ctx, map[string]string{
		"action":        "chat",
		"target_remark": targetRemark,
		"persona":       persona,
		"user_message":  userMsg,
		"reply":         reply,
		"addr":          c.addr,
	})
	return err
}

func (c *Client) PollMessage(ctx context.Context, targetRemark string) (PollResult, error) {
	out, err := c.call(ctx, map[string]string{
		"action":        "poll",
		"target_remark": targetRemark,
		"addr":          c.addr,
	})
	if err != nil {
		return PollResult{}, err
	}

	var res struct {
		HasNew  bool   `json:"has_new"`
		Message string `json:"message"`
	}
	if err := json.Unmarshal(out, &res); err != nil {
		return PollResult{}, fmt.Errorf("parse poll result failed: %w, output=%s", err, string(out))
	}
	return PollResult{HasNew: res.HasNew, Message: res.Message}, nil
}

func (c *Client) call(ctx context.Context, payload map[string]string) ([]byte, error) {
	b, err := json.Marshal(payload)
	if err != nil {
		return nil, err
	}

	cmd := exec.CommandContext(ctx, "python3", "python/grpc_client.py", string(b))
	out, err := cmd.CombinedOutput()
	if err != nil {
		return nil, fmt.Errorf("grpc bridge helper failed: %w, output=%s", err, string(out))
	}
	return out, nil
}
