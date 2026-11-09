// Command researchos is the ResearchOS-owned CLI entry (W02-03 thin launcher).
// It reuses the upstream Mu/Pi starter for the interactive worker (attached later);
// this entry provides real version/help/doctor behavior and explicit NOT_IMPLEMENTED
// for capabilities owned by later cards. It never starts a second business scheduler.
// W05-03 extended it: non-interactive stdout is JSONL only, an empty argv is the contract's
// interactive command, and the host-bound verbs send client-protocol commands through
// apps/cli/cli_v2.go instead of reporting a health probe as a result.
package main

import (
	"os"
	"strings"
)

const (
	productName    = "researchos"
	buildVersion   = "0.2.4-w0203"
	clientProtocol = "researchos-client/2"
	discoveryPath  = ".local/v24_host.json"
)

type discovery struct {
	URL       string `json:"url"`
	PID       int    `json:"pid"`
	DataDir   string `json:"data_dir"`
	StartedAt string `json:"started_at"`
}

func main() {
	args := os.Args[1:]
	cmd := ""
	if len(args) > 0 {
		cmd = args[0]
	}
	if err := initProductLayout(); err != nil {
		fail("startup", exitFailed, "PRODUCT_LAYOUT_INVALID", err.Error())
	}
	// A product CLI owns no scheduler. Host-bound commands first discover or
	// start the same per-user Electron parent that owns Core's private pipe.
	if requiresProductHost(cmd, args[1:]...) {
		if err := ensureProductHost(); err != nil {
			fail(cmd, exitFailed, "PRODUCT_HOST_UNAVAILABLE", err.Error())
		}
	}
	// The contract writes the interactive entry as `researchos [--project <path-or-id>]`, so an empty argv and a
	// leading flag are the interactive command, not a help page. `chat` is not a contract command at all.
	if cmd == "" || cmd == "--project" {
		cliInteractive(args)
		return
	}
	switch cmd {
	case "version", "--version":
		// W05-03 output contract: non-interactive stdout is JSONL only, so the human-readable line is a diagnostic.
		diag("%s %s protocol=%s", productName, buildVersion, clientProtocol)
		outJSON(map[string]any{"command": "version", "status": "COMPLETED", "exit_code": 0,
			"product": productName, "version": buildVersion, "protocol": clientProtocol})
	case "help", "--help":
		cliHelpSurface(true)
	case "doctor":
		cliDoctor()
	case "task":
		runCodingTask(args[1:])
	default:
		if h, registered := commandHandlers[cmd]; registered {
			h(args[1:])
			return
		}
		diag("%s: NOT_IMPLEMENTED (%s is registered to a later card; no silent success)", cmd, cmd)
		outJSON(map[string]any{"command": cmd, "status": "REJECTED", "exit_code": 3,
			"reason": "NOT_IMPLEMENTED", "detail": cmd + " is registered to a later card; no silent success"})
		os.Exit(3)
	}
}

func requiresProductHost(cmd string, rest ...string) bool {
	switch cmd {
	case "doctor", "version", "--version", "help", "--help", "/help", "commands":
		return false
	case "config":
		return len(rest) > 0 && rest[0] == "set-model"
	case "/model":
		return true
	}
	if cmd == "" || cmd == "--project" || cmd == "task" || cmd == "run" || cmd == "worker" {
		return true
	}
	row, registered := contractCommands[cmd]
	return registered && strings.Contains(row.needs, "host")
}
