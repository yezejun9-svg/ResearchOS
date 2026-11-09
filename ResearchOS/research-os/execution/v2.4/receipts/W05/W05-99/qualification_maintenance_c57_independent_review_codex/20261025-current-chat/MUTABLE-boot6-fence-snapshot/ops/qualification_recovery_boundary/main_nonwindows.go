//go:build !windows

package main

import (
	"encoding/json"
	"os"
)

func main() {
	_ = json.NewEncoder(os.Stdout).Encode(map[string]string{
		"schema": "researchos.recovery-boundary-helper-result.v1",
		"error":  "qualification recovery boundary is unsupported outside Windows",
	})
	os.Exit(1)
}
