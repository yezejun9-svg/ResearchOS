//go:build !windows

package main

import "path/filepath"

func initProductLayout() error     { return nil }
func productInstalled() bool       { return false }
func productDiscoveryFile() string { return cliEnv("RESEARCHOS_CLI_DISCOVERY", discoveryPath) }
func productConfigFile() string {
	return cliEnv("RESEARCHOS_CLI_CONFIG", filepath.Join(".local", "v24_cli_config.json"))
}
func ensureProductHost() error { return nil }
