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
		fmt.Printf("%s %s protocol=%s\n", productName, buildVersion, clientProtocol)
	case "help", "--help", "":
		fmt.Printf("%s %s (protocol %s)\n\nusage: researchos <command>\n\n", productName, buildVersion, clientProtocol)
		fmt.Println("available now:")
		fmt.Println("  version   product/protocol version")
		fmt.Println("  help      this help")
		fmt.Println("  doctor    host discovery + health + protocol handshake")
		fmt.Println("planned (owned by later cards; NOT_IMPLEMENTED here):")
		for _, c := range []string{"init", "status", "resume", "cancel", "config", "chat (interactive TUI)", "run --output jsonl", "/goal"} {
			fmt.Printf("  %-28s NOT_IMPLEMENTED\n", c)
		}
	case "doctor":
		b, err := os.ReadFile(discoveryPath)
		if err != nil {
			fmt.Println("doctor: host discovery NOT_FOUND at", discoveryPath)
			os.Exit(3)
		}
		var d discovery
		if err := json.Unmarshal(b, &d); err != nil {
			fmt.Println("doctor: discovery file INVALID_JSON")
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
	default:
		fmt.Printf("%s: NOT_IMPLEMENTED (%s is registered to a later card; no silent success)\n", cmd, cmd)
		os.Exit(3)
	}
}
