//go:build windows

package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"time"

	"researchos.local/research-os/internal/ownedcorestop"
)

func main() { os.Exit(run(os.Args[1:])) }

func run(args []string) int {
	if len(args) == 0 {
		fmt.Fprintln(os.Stderr, "usage: owned_core_stop preflight|commit|inspect")
		return 2
	}
	ctx, cancel := context.WithTimeout(context.Background(), 45*time.Second)
	defer cancel()
	var result any
	var err error
	switch args[0] {
	case "preflight":
		fs := flag.NewFlagSet("preflight", flag.ContinueOnError)
		input := fs.String("input", "", "strict subject JSON")
		operationID := fs.String("operation-id", "", "exact operation ID")
		out := fs.String("out", "", "new private directory outside data root")
		if fs.Parse(args[1:]) != nil || fs.NArg() != 0 || *input == "" || *operationID == "" || *out == "" {
			return 2
		}
		var plan ownedcorestop.Plan
		var sha string
		plan, sha, err = ownedcorestop.Preflight(ctx, *input, *operationID, *out)
		if err == nil {
			result = struct {
				Plan       ownedcorestop.Plan `json:"plan"`
				PlanSHA256 string             `json:"plan_sha256"`
			}{plan, sha}
		}
	case "commit":
		fs := flag.NewFlagSet("commit", flag.ContinueOnError)
		plan := fs.String("plan", "", "reviewed plan.json")
		sha := fs.String("expect-plan-sha256", "", "exact reviewed SHA256")
		if fs.Parse(args[1:]) != nil || fs.NArg() != 0 || *plan == "" || *sha == "" {
			return 2
		}
		result, err = ownedcorestop.Commit(ctx, *plan, *sha)
	case "inspect":
		fs := flag.NewFlagSet("inspect", flag.ContinueOnError)
		plan := fs.String("plan", "", "plan.json")
		if fs.Parse(args[1:]) != nil || fs.NArg() != 0 || *plan == "" {
			return 2
		}
		result, err = ownedcorestop.Inspect(*plan)
	default:
		fmt.Fprintln(os.Stderr, "unknown command")
		return 2
	}
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		return 1
	}
	if err = json.NewEncoder(os.Stdout).Encode(result); err != nil {
		fmt.Fprintln(os.Stderr, err)
		return 1
	}
	if r, ok := result.(ownedcorestop.Result); ok && r.State != "STOPPED_LEASE_VERIFIED" {
		return 3
	}
	return 0
}
