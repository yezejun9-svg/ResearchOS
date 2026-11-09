//go:build windows

package main

import (
	"context"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"os"

	"researchos.local/research-os/internal/recoveryboundary"
)

type result struct {
	Schema string `json:"schema"`
	State  string `json:"state,omitempty"`
	Error  string `json:"error,omitempty"`
}

func parse(args []string) (phase, root, operation, plan string, err error) {
	if len(args) == 0 {
		return "", "", "", "", errors.New("one fixed phase required")
	}
	phase = args[0]
	if phase != "plan" && phase != "arm" && phase != "observe" && phase != "status" && phase != "disarm-request" {
		return "", "", "", "", errors.New("unsupported phase")
	}
	f := flag.NewFlagSet(phase, flag.ContinueOnError)
	f.SetOutput(os.Stderr)
	f.StringVar(&root, "data-root", "", "frozen data root")
	f.StringVar(&operation, "operation-id", "", "frozen operation")
	f.StringVar(&plan, "plan-sha256", "", "frozen boundary plan digest")
	if err = f.Parse(args[1:]); err != nil {
		return
	}
	if len(f.Args()) != 0 || root == "" || operation == "" || plan == "" {
		err = errors.New("exact data-root, operation-id and plan-sha256 required")
	}
	return
}

func run(ctx context.Context, args []string) (string, error) {
	phase, root, operation, plan, err := parse(args)
	if err != nil {
		return "", err
	}
	return recoveryboundary.RunPhase(ctx, phase, root, operation, plan)
}

func main() {
	state, err := run(context.Background(), os.Args[1:])
	out := result{Schema: "researchos.recovery-boundary-helper-result.v1", State: state}
	if err != nil {
		out.Error = err.Error()
	}
	if e := json.NewEncoder(os.Stdout).Encode(out); e != nil {
		fmt.Fprintln(os.Stderr, e)
		os.Exit(2)
	}
	if err != nil {
		os.Exit(1)
	}
}
