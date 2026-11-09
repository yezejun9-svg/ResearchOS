// apps/cli/cli_run_contract.go reconciles the two meanings `researchos run` carries.
//
// The accepted W05-02 card delivered `run` as the Job Object cancel cascade (flags -dir/-job/-queue/...), and its
// check drives that verb by name. contracts/product.contract.json declares a different required command with the same
// word: `researchos run <prompt> --project <id> --output jsonl`, whose local operations are session.send and
// session.events. Both must work, so this file dispatches on the shape the user actually typed and delegates to the
// accepted handler rather than replacing it. W0503-ACCEPTED-VERBS-NOT-SHADOWED is what proves the delegation is real:
// it drives the accepted cascade through this dispatcher and grades the stage order the accepted check grades.
package main

import "strings"

// acceptedRun is set by the windows build, where cancel_run_windows.go owns the cascade. On any other build it stays
// nil, and a cascade-shaped invocation falls through to the contract path and reports its own refusal instead of
// pretending a job object exists.
var acceptedRun func([]string)

func init() {
	// This file sorts after cancel_run_windows.go, so the accepted registration is already in the map; replacing it
	// here is a delegation, and the accepted handler is the one that still answers accepted-shaped arguments.
	commandHandlers["run"] = runDispatch
}

var acceptedRunFlags = []string{"-dir", "-job", "-queue", "-tick-file", "-exe", "-cancel-after", "-settle",
	"-observe-after"}

func looksLikeAcceptedRun(args []string) bool {
	for _, a := range args {
		for _, f := range acceptedRunFlags {
			if a == f || strings.HasPrefix(a, f+"=") {
				return true
			}
		}
	}
	// A bare `researchos run` with no prompt is the accepted cascade's own default invocation.
	_, has := firstPositional(args)
	return !has
}

func runDispatch(args []string) {
	if out, has := flagValue(args, "output"); has && out != "jsonl" {
		fail("run", exitUsage, "OUTPUT_FORMAT_UNSUPPORTED",
			"the contract's headless format is JSONL; --output accepts only jsonl, got "+out)
	}
	if acceptedRun != nil && looksLikeAcceptedRun(args) {
		acceptedRun(args)
		return
	}
	cliHostCommand("run", args)
}
