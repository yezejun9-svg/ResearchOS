//go:build windows

package main

import (
	"context"
	"encoding/json"
	"errors"
	"os"
	"strings"
	"time"

	"researchos.local/research-os/internal/host"
)

func parseQualificationMaintenance(args []string) (host.QualificationMaintenanceInput, error) {
	var input host.QualificationMaintenanceInput
	if len(args) < 2 || args[0] != "--qualification-failure-maintenance" {
		return input, errors.New("qualification maintenance action required")
	}
	input.Action = args[1]
	fields := map[string]*string{"data-root": &input.DataRoot}
	required := []string{"data-root"}
	switch input.Action {
	case "preflight":
		fields["proposal"] = &input.Proposal
		fields["out"] = &input.Out
		required = append(required, "proposal", "out")
	case "commit", "recover", "abort":
		fields["plan"] = &input.Plan
		fields["plan-sha256"] = &input.PlanSHA256
		fields["operation-id"] = &input.OperationID
		required = append(required, "plan", "plan-sha256", "operation-id")
	default:
		return input, errors.New("qualification maintenance action unsupported")
	}
	seen := map[string]bool{}
	for i := 2; i < len(args); i++ {
		arg := args[i]
		if !strings.HasPrefix(arg, "--") {
			return input, errors.New("qualification maintenance positional argument")
		}
		key, value, hasValue := strings.Cut(strings.TrimPrefix(arg, "--"), "=")
		dest, ok := fields[key]
		if !ok || seen[key] {
			return input, errors.New("qualification maintenance mixed or duplicate argument")
		}
		seen[key] = true
		if !hasValue {
			i++
			if i >= len(args) || strings.HasPrefix(args[i], "--") {
				return input, errors.New("qualification maintenance missing value")
			}
			value = args[i]
		}
		if value == "" {
			return input, errors.New("qualification maintenance empty value")
		}
		*dest = value
	}
	for _, name := range required {
		if !seen[name] {
			return input, errors.New("qualification maintenance required argument missing")
		}
	}
	return input, nil
}

func runQualificationFailureMaintenance(args []string) (bool, error) {
	if len(args) == 0 || args[0] != "--qualification-failure-maintenance" {
		return false, nil
	}
	input, err := parseQualificationMaintenance(args)
	if err != nil {
		return true, err
	}
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Minute)
	defer cancel()
	result, err := host.RunQualificationFailureMaintenance(ctx, input)
	if err != nil {
		return true, err
	}
	return true, json.NewEncoder(os.Stdout).Encode(result)
}
