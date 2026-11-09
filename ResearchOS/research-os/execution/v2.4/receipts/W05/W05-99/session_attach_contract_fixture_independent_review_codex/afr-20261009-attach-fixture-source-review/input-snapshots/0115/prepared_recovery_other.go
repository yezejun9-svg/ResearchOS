//go:build !windows

package main

import "errors"

func runPreparedRecoveryMaintenance(args []string) (bool, error) {
	if len(args) > 0 && (args[0] == "--private-prepared-abandonment" || args[0] == "--private-prepared-schema23-to24") {
		return true, errors.New("private recovery requires Windows")
	}
	return false, nil
}
