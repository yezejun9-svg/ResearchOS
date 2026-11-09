//go:build !windows

package main

import "errors"

func runQualificationFailureMaintenance(args []string) (bool, error) {
	if len(args) == 0 || args[0] != "--qualification-failure-maintenance" {
		return false, nil
	}
	return true, errors.New("qualification failure maintenance requires Windows")
}
