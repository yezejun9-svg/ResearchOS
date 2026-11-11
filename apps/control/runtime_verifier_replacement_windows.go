//go:build windows

package main

import (
	"context"
	"encoding/json"
	"errors"
	"io"
	"strings"
	"time"

	rt "researchos.local/research-os/adapters/runtime"
	"researchos.local/research-os/internal/host"
)

func parseRuntimeVerifierReplacement(args []string) (host.RuntimeVerifierReplacementInput, error) {
	var in host.RuntimeVerifierReplacementInput
	if len(args) < 2 || args[0] != "--runtime-verifier-replacement" {
		return in, errors.New("replacement action required")
	}
	in.Action = args[1]
	fields := map[string]*string{"data-root": &in.DataRoot}
	required := []string{"data-root"}
	switch in.Action {
	case "preflight":
		fields["manifest"] = &in.Manifest
		fields["expect-record-sha256"] = &in.ExpectRecordSHA256
		fields["expect-manifest-sha256"] = &in.ExpectManifestSHA256
		fields["operation-id"] = &in.OperationID
		fields["out"] = &in.Out
		fields["rollback-of"] = &in.RollbackOf
		required = append(required, "manifest", "expect-record-sha256", "expect-manifest-sha256", "operation-id", "out")
	case "commit", "recover":
		fields["plan"] = &in.Plan
		fields["expect-plan-sha256"] = &in.ExpectPlanSHA256
		required = append(required, "plan", "expect-plan-sha256")
		if in.Action == "recover" {
			fields["operation-id"] = &in.OperationID
			fields["action"] = &in.RecoveryAction
			required = append(required, "operation-id", "action")
		}
	default:
		return in, errors.New("unknown replacement action")
	}
	seen := map[string]bool{}
	for i := 2; i < len(args); i++ {
		arg := args[i]
		if !strings.HasPrefix(arg, "--") {
			return in, errors.New("positional/mixed arguments refused")
		}
		key, value, hasValue := strings.Cut(strings.TrimPrefix(arg, "--"), "=")
		dest, ok := fields[key]
		if !ok || seen[key] {
			return in, errors.New("unknown or duplicate argument")
		}
		seen[key] = true
		if !hasValue {
			i++
			if i >= len(args) || strings.HasPrefix(args[i], "--") {
				return in, errors.New("argument value missing")
			}
			value = args[i]
		}
		if value == "" {
			return in, errors.New("empty argument refused")
		}
		*dest = value
	}
	for _, key := range required {
		if !seen[key] {
			return in, errors.New("required argument missing")
		}
	}
	return in, nil
}
func runRuntimeVerifierReplacement(args []string, out io.Writer) (bool, int) {
	if len(args) == 0 || args[0] != "--runtime-verifier-replacement" {
		return false, 0
	}
	in, e := parseRuntimeVerifierReplacement(args)
	if e != nil {
		_ = json.NewEncoder(out).Encode(host.RuntimeVerifierReplacementResult{Schema: "researchos.runtime-verifier-replacement.v1", Action: in.Action, State: "REJECTED", Outcome: "NOT_APPLIED", ErrorCode: "REPLACEMENT_ARGUMENTS"})
		return true, 2
	}
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	result, e := host.RuntimeVerifierReplacement(ctx, in)
	if writeErr := json.NewEncoder(out).Encode(result); writeErr != nil {
		return true, 1
	}
	if e != nil {
		return true, 1
	}
	return true, 0
}
func runtimeVerifierReplacementStartupGate(lease *rt.DataRootLease) error {
	return host.RuntimeVerifierReplacementStartupGate(lease)
}
