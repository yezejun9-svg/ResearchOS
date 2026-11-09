//go:build windows

package main

import (
	"context"
	"os"
	"time"

	"golang.org/x/sys/windows"
	"researchos.local/research-os/internal/verifier"
)

// Only inherited anonymous pipes are accepted. No token CLI option, config,
// environment lookup, model client, or arbitrary verification command exists.
func main() {
	if len(os.Args) != 1 {
		os.Exit(2)
	}
	for _, f := range []*os.File{os.Stdin, os.Stdout} {
		kind, e := windows.GetFileType(windows.Handle(f.Fd()))
		if e != nil || kind != windows.FILE_TYPE_PIPE {
			os.Exit(2)
		}
	}
	challenge, e := verifier.Handshake(os.Stdin, os.Stdout)
	if e != nil {
		os.Exit(2)
	}
	var job verifier.Job
	if verifier.ReadFrame(os.Stdin, &job) != nil || job.Nonce != challenge.Nonce || job.Protocol != challenge.Protocol {
		os.Exit(2)
	}
	ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
	defer cancel()
	result, e := verifier.Verify(ctx, job)
	job.Token = ""
	if verifier.WriteFrame(os.Stdout, result) != nil || e != nil {
		os.Exit(1)
	}
}
