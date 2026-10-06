//go:build windows

// A disposable long-lived process for native supervisor mechanism tests.
package main

import (
	"os"
	"path/filepath"
	"time"
)

var variant = "stable"

func main() {
	if len(os.Args) != 3 || os.Args[1] == "" || !filepath.IsAbs(os.Args[2]) || variant == "" {
		os.Exit(2)
	}
	for {
		time.Sleep(time.Hour)
	}
}
