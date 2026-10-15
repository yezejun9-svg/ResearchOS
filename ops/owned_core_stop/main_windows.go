//go:build windows

package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"strings"
	"time"

	"researchos.local/research-os/internal/ownedcorestop"
)

func main() { os.Exit(run(os.Args[1:])) }

func parseCommand(args []string) (string, map[string]string, error) {
	if len(args) == 0 {
		return "", nil, errors.New("one action required")
	}
	action := args[0]
	var required []string
	switch action {
	case "preflight":
		required = []string{"--input", "--operation-id", "--out"}
	case "commit":
		required = []string{"--plan", "--expect-plan-sha256"}
	case "inspect":
		required = []string{"--plan"}
	default:
		return "", nil, errors.New("unknown action")
	}
	if len(args) != 1+2*len(required) {
		return "", nil, errors.New("exact action flags required")
	}
	allowed := make(map[string]bool, len(required))
	for _, k := range required {
		allowed[k] = true
	}
	parsed := make(map[string]string, len(required))
	for i := 1; i < len(args); i += 2 {
		key, value := args[i], args[i+1]
		_, seen := parsed[key]
		if !allowed[key] || seen || value == "" || strings.HasPrefix(value, "--") || strings.ContainsRune(value, '\x00') {
			return "", nil, errors.New("mixed, duplicate, or malformed flags")
		}
		parsed[key] = value
	}
	if len(parsed) != len(required) {
		return "", nil, errors.New("missing action flag")
	}
	return action, parsed, nil
}

func run(args []string) int {
	action, flags, parseErr := parseCommand(args)
	if parseErr != nil {
		fmt.Fprintln(os.Stderr, parseErr)
		return 2
	}
	ctx, cancel := context.WithTimeout(context.Background(), 45*time.Second)
	defer cancel()
	var result any
	var err error
	switch action {
	case "preflight":
		var plan ownedcorestop.Plan
		var sha string
		plan, sha, err = ownedcorestop.Preflight(ctx, flags["--input"], flags["--operation-id"], flags["--out"])
		if err == nil {
			result = struct {
				Plan       ownedcorestop.Plan `json:"plan"`
				PlanSHA256 string             `json:"plan_sha256"`
			}{plan, sha}
		}
	case "commit":
		result, err = ownedcorestop.Commit(ctx, flags["--plan"], flags["--expect-plan-sha256"])
	case "inspect":
		result, err = ownedcorestop.Inspect(flags["--plan"])
	}
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		return 1
	}
	if err = json.NewEncoder(os.Stdout).Encode(result); err != nil {
		fmt.Fprintln(os.Stderr, err)
		return 1
	}
	if r, ok := result.(ownedcorestop.Result); ok && r.State != "STOPPED_LEASE_VERIFIED" && r.State != "PREFLIGHT_COMPLETE" {
		return 3
	}
	return 0
}
