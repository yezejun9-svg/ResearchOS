//go:build windows

// runtime is a worker for a single already-admitted Run, never a Task scheduler.
package main

import (
	"bufio"
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"os/signal"
	"time"

	rt "researchos.local/research-os/adapters/runtime"
)

func main() { os.Exit(run()) }
func run() int {
	request := flag.String("request", "", "private admitted-run request JSON")
	journal := flag.String("journal", "", "new run journal directory")
	reconcile := flag.Bool("reconcile", false, "inspect existing journal without launching")
	flag.Parse()
	if *journal == "" {
		fmt.Fprintln(os.Stderr, "journal required")
		return 2
	}
	if *reconcile {
		j, e := rt.Reconcile(*journal)
		if e != nil {
			fmt.Fprintln(os.Stderr, e)
			return 1
		}
		json.NewEncoder(os.Stdout).Encode(j)
		if j.State == "UNKNOWN" {
			return 1
		}
		return 0
	}
	b, e := os.ReadFile(*request)
	if e != nil {
		fmt.Fprintln(os.Stderr, e)
		return 2
	}
	var input struct {
		Spec           rt.Spec  `json:"spec"`
		Inputs         []string `json:"inputs"`
		CodexHome      string   `json:"codex_home"`
		TimeoutSeconds int      `json:"timeout_seconds"`
	}
	if e = json.Unmarshal(b, &input); e != nil || len(input.Inputs) != len(input.Spec.Commands) {
		fmt.Fprintln(os.Stderr, "valid request and one input per command required")
		return 2
	}
	for i := range input.Spec.Commands {
		input.Spec.Commands[i].Input = input.Inputs[i]
	}
	input.Spec.Environment = rt.Environment(input.CodexHome)
	if input.TimeoutSeconds > 0 {
		input.Spec.Timeout = time.Duration(input.TimeoutSeconds) * time.Second
	}
	w, e := rt.Start(*journal, input.Spec)
	if e != nil {
		fmt.Fprintln(os.Stderr, e)
		return 1
	}
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt)
	defer stop()
	// Coordinator renew/cancel frames contain an epoch, never credentials. EOF does not renew a lease.
	go func() {
		scanner := bufio.NewScanner(os.Stdin)
		for scanner.Scan() {
			var frame struct {
				Operation string `json:"operation"`
				Epoch     int64  `json:"epoch"`
				Reason    string `json:"reason"`
			}
			if json.Unmarshal(scanner.Bytes(), &frame) != nil {
				continue
			}
			switch frame.Operation {
			case "renew":
				w.Renew(frame.Epoch, rt.LeaseDuration)
			case "cancel":
				w.Cancel(frame.Epoch, frame.Reason)
			}
		}
	}()
	j, e := w.Wait(ctx)
	if e != nil {
		w.Cancel(input.Spec.Epoch, "worker interrupted")
		deadline, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()
		j, e = w.Wait(deadline)
	}
	json.NewEncoder(os.Stdout).Encode(j)
	if e != nil || j.State == "UNKNOWN" || j.State == "FAILED" {
		return 1
	}
	return 0
}
