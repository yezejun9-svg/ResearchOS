package main

// apps/cli/cli_http.go holds the only outbound call the CLI command surface makes: a health probe against the host
// the discovery file names. It is separate from cli_contract.go because the accepted W02-03 launcher already owns
// net/http usage for doctor; this file never starts a process and never shells out, so the card negative "shell
// alias delegating to another vendor CLI" cannot become true here by construction.

import (
	"io"
	"net/http"
	"time"
)

func hostGet(url string) (int, string, error) {
	client := http.Client{Timeout: 6 * time.Second}
	resp, err := client.Get(url)
	if err != nil {
		return 0, "", err
	}
	defer resp.Body.Close()
	raw, readErr := io.ReadAll(io.LimitReader(resp.Body, 4096))
	return resp.StatusCode, string(raw), readErr
}
