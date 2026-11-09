//go:build windows

package main

import (
	"bufio"
	"encoding/json"
	"errors"
	"os"
	"strings"
	"time"

	"golang.org/x/sys/windows"
)

// The copied chooser depends on this production error sentinel's text.
var ErrFrameShape = errors.New("INVALID_REQUEST")

type observation struct {
	Event        string `json:"event"`
	PID          uint32 `json:"pid"`
	StartupFlags uint32 `json:"startup_flags,omitempty"`
	StartupShow  uint16 `json:"startup_show"`
	ElapsedNS    int64  `json:"elapsed_ns,omitempty"`
	Chosen       string `json:"chosen,omitempty"`
	Error        string `json:"error,omitempty"`
}

func emit(event observation) error {
	event.PID = windows.GetCurrentProcessId()
	return json.NewEncoder(os.Stdout).Encode(event)
}

func main() {
	if len(os.Args) != 2 || !strings.Contains(os.Args[1], `项目 空间`) {
		os.Exit(2)
	}
	var startup windows.StartupInfo
	if err := windows.GetStartupInfo(&startup); err != nil {
		os.Exit(3)
	}
	if err := emit(observation{Event: "ready", StartupFlags: startup.Flags, StartupShow: startup.ShowWindow}); err != nil {
		os.Exit(4)
	}
	scanner := bufio.NewScanner(os.Stdin)
	if !scanner.Scan() || scanner.Text() != "open" {
		os.Exit(5)
	}
	begin := time.Now()
	chosen, err := chooseNativeFolderWindows(os.Args[1])
	result := observation{Event: "result", ElapsedNS: time.Since(begin).Nanoseconds(), Chosen: chosen}
	if err != nil {
		result.Error = err.Error()
	}
	if emit(result) != nil {
		os.Exit(6)
	}
}
