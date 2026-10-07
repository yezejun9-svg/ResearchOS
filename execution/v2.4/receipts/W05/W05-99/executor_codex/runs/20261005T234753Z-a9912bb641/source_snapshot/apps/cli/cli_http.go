package main

// apps/cli/cli_http.go holds the CLI's plain GET helper, shared by the accepted launcher's `doctor` health probe and
// nothing else: the command verbs themselves speak the client protocol through apps/cli/cli_v2.go, which POSTs an
// envelope to /v2/command. This file never starts a process and never shells out, so the card negative "shell alias
// delegating to another vendor CLI" cannot become true here by construction.

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
