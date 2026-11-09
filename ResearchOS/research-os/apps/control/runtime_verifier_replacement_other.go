//go:build !windows

package main

import (
	"fmt"
	"io"
)

func runRuntimeVerifierReplacement(args []string, out io.Writer) (bool, int) {
	if len(args) == 0 || args[0] != "--runtime-verifier-replacement" {
		return false, 0
	}
	fmt.Fprintln(out, `{"schema":"researchos.runtime-verifier-replacement.v1","state":"REJECTED","outcome":"NOT_APPLIED","error_code":"WINDOWS_REQUIRED"}`)
	return true, 2
}
func runtimeVerifierReplacementStartupGate(lease any) error { return nil }
