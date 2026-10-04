// Command researchos is the ResearchOS-owned CLI entry (W02-03 thin launcher).
// It reuses the upstream Mu/Pi starter for the interactive worker (attached later);
// this entry provides real version/help/doctor behavior and explicit NOT_IMPLEMENTED
// for capabilities owned by later cards. It never starts a second business scheduler.
package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"time"
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
	switch cmd {
	case "version", "--version":
		// W05-03 output contract: non-interactive stdout is JSONL only, so the human-readable line is a diagnostic.
		diag("%s %s protocol=%s", productName, buildVersion, clientProtocol)
		outJSON(map[string]any{"command": "version", "status": "COMPLETED", "exit_code": 0,
			"product": productName, "version": buildVersion, "protocol": clientProtocol})
	case "help", "--help", "":
		cliHelpSurface(true)
	case "doctor":
		b, err := os.ReadFile(discoveryPath)
		if err != nil {
			diag("doctor: host discovery NOT_FOUND at %s", discoveryPath)
			outJSON(map[string]any{"command": "doctor", "status": "REJECTED", "exit_code": 3,
				"reason": "NOT_FOUND", "detail": discoveryPath + ": " + err.Error()})
			os.Exit(3)
		}
		var d discovery
		if err := json.Unmarshal(b, &d); err != nil {
			diag("doctor: discovery file INVALID_JSON")
			outJSON(map[string]any{"command": "doctor", "status": "REJECTED", "exit_code": 3,
				"reason": "INVALID_JSON", "detail": discoveryPath})
			os.Exit(3)
		}
		status := "DOWN"
		code := 0
		client := http.Client{Timeout: 4 * time.Second}
		resp, err := client.Get(d.URL + "/healthz")
		if err == nil {
			resp.Body.Close()
			if resp.StatusCode == 200 {
				status = "UP"
			} else {
				code = resp.StatusCode
			}
		}
		out := map[string]any{"product": productName, "version": buildVersion,
			"client_protocol": clientProtocol, "host_url": d.URL, "host_pid": d.PID,
			"host_data_dir": d.DataDir, "health": status}
		if status != "UP" {
			out["http_code"] = code
		}
		line, _ := json.Marshal(out)
		fmt.Println(string(line))
		if status != "UP" {
			os.Exit(4)
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
