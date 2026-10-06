//go:build windows

package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	sandbox "researchos.local/research-os/ops/experiment_sandbox"
	"time"
)

func main() {
	if len(os.Args) != 3 {
		fmt.Fprintln(os.Stderr, "usage: sandbox command.json receipt.json")
		os.Exit(2)
	}
	b, e := os.ReadFile(os.Args[1])
	if e != nil {
		panic(e)
	}
	var c sandbox.Command
	if e = json.Unmarshal(b, &c); e != nil {
		panic(e)
	}
	if c.Timeout == 0 {
		c.Timeout = 90 * time.Second
	}
	r, e := sandbox.Run(context.Background(), c)
	out := map[string]any{"command": c, "receipt": r, "error": nil}
	if e != nil {
		out["error"] = e.Error()
	}
	b, _ = json.MarshalIndent(out, "", "  ")
	if e2 := os.WriteFile(os.Args[2], b, 0600); e2 != nil {
		panic(e2)
	}
	fmt.Println(string(b))
	if e != nil || r.ExitCode != 0 || !r.Stopped {
		os.Exit(1)
	}
}
