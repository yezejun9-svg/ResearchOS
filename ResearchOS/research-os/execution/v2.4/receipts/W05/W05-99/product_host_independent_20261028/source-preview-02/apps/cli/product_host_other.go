//go:build !windows

package main

import (
	"path/filepath"
	"researchos.local/research-os/internal/host"
)

func initProductLayout() error     { return nil }
func productInstalled() bool       { return false }
func productDiscoveryFile() string { return cliEnv("RESEARCHOS_CLI_DISCOVERY", discoveryPath) }
func productConfigFile() string {
	return cliEnv("RESEARCHOS_CLI_CONFIG", filepath.Join(".local", "v24_cli_config.json"))
}
func ensureProductHost() error                        { return nil }
func productGuardPath(string) error                   { return nil }
func productDoctorIdentity(discovery) (string, error) { return "", nil }
func productNativeRequest(id string, request []byte) ([]byte, error) {
	return cliNativeDial(host.PipeName(id), request)
}
