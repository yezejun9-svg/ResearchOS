//go:build windows

// apps/cli/cli_run_windows.go binds the accepted W05-02 cascade handler so cli_run_contract.go can delegate to it.
// It is a separate file because cancel_run_windows.go is behind a windows build tag: naming runCancelCascade from an
// untagged file would break every other platform's build.

package main

func init() { acceptedRun = runCancelCascade }
