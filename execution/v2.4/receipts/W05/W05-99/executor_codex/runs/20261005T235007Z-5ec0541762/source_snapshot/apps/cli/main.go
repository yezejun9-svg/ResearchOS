// Command researchos is the ResearchOS-owned CLI entry (W02-03 thin launcher).
// It reuses the upstream Mu/Pi starter for the interactive worker (attached later);
// this entry provides real version/help/doctor behavior and explicit NOT_IMPLEMENTED
// for capabilities owned by later cards. It never starts a second business scheduler.
// W05-03 extended it: non-interactive stdout is JSONL only, an empty argv is the contract's
// interactive command, and the host-bound verbs send client-protocol commands through
// apps/cli/cli_v2.go instead of reporting a health probe as a result.
package main

import (
	"encoding/json"
	"fmt"
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
	// The contract writes the interactive entry as `researchos [--project <path-or-id>]`, so an empty argv and a
	// leading flag are the interactive command, not a help page. `chat` is not a contract command at all.
	if cmd == "" || (strings.HasPrefix(cmd, "--") && cmd != "--version" && cmd != "--help") {
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
		// The same discovery path every other verb honours: RESEARCHOS_CLI_DISCOVERY names the file, so doctor can be
		// pointed at the host a check actually started instead of only at the repository default.
		discoveryFile := cliEnv("RESEARCHOS_CLI_DISCOVERY", discoveryPath)
		b, err := os.ReadFile(discoveryFile)
		if err != nil {
			diag("doctor: host discovery NOT_FOUND at %s", discoveryFile)
			outJSON(map[string]any{"command": "doctor", "status": "REJECTED", "exit_code": 3,
				"reason": "NOT_FOUND", "detail": discoveryFile + ": " + err.Error(), "discovery_path": discoveryFile})
			os.Exit(3)
		}
		var d discovery
		if err := json.Unmarshal(b, &d); err != nil {
			diag("doctor: discovery file INVALID_JSON")
			outJSON(map[string]any{"command": "doctor", "status": "REJECTED", "exit_code": 3,
				"reason": "INVALID_JSON", "detail": discoveryFile, "discovery_path": discoveryFile})
			os.Exit(3)
		}
		status := "DOWN"
		code := 0
		probe := ""
		health, body, err := hostGet(d.URL + "/healthz")
		if err != nil {
			probe = err.Error()
		} else {
			probe = clip(body, 200)
			if health == 200 {
				status = "UP"
			} else {
				code = health
			}
		}
		out := map[string]any{"command": "doctor", "status": map[string]any{"UP": "COMPLETED", "DOWN": "REJECTED"}[status],
			"exit_code": map[string]any{"UP": 0, "DOWN": 1}[status], "product": productName, "version": buildVersion,
			"client_protocol": clientProtocol, "host_url": d.URL, "host_pid": d.PID, "host_data_dir": d.DataDir,
			"health": status, "discovery_path": discoveryFile, "probe": probe}
		if status != "UP" {
			out["http_code"] = code
			// Exit 4 is the shape the accepted W02-03 launcher shipped for an unhealthy host. It sits outside the
			// 0/1/2/3/130 vocabulary this card's action names, and it is left as delivered rather than silently
			// renumbered: the receipt records the deviation with the row that measures it (W0503-DOCTOR-DOWN-EXIT-4).
			out["exit_code_note"] = "an unhealthy host is 1 (execution_or_check_failed) per contracts/product.contract.json cli.exit_codes; the accepted W02-03 launcher shipped 4 here, and 4 is not in that map"
		}
		line, _ := json.Marshal(out)
		fmt.Println(string(line))
		if status != "UP" {
			os.Exit(1)
		}
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
