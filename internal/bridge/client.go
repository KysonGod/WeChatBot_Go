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

func New(_ context.Context, addr string) (*Client, error) {
	return &Client{addr: addr}, nil
}

func (c *Client) Close() error { return nil }

func (c *Client) SendToWX(ctx context.Context, targetRemark, persona, userMsg, reply string) error {
	payload := map[string]string{
		"target_remark": targetRemark,
		"persona":       persona,
		"user_message":  userMsg,
		"reply":         reply,
		"addr":          c.addr,
	}
	b, err := json.Marshal(payload)
	if err != nil {
		return err
	}

	cmd := exec.CommandContext(ctx, "python3", "python/grpc_client.py", string(b))
	out, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("grpc bridge helper failed: %w, output=%s", err, string(out))
	}
	return nil
}
