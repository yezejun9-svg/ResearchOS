// Public W16 test executable. Each candidate is separately built and hash sealed.
package main

import (
	"encoding/json"
	"os"
	"path/filepath"
	"researchos.local/research-os/evaluation/evolution"
	"time"
)

var variant = "stable"

func main() {
	// R2 tests use the exact previously evaluated bytes as a disposable
	// long-lived process. This mode has no product API, task dispatch or LIVE
	// authority; the normal single-request evaluation path remains unchanged.
	if len(os.Args) == 4 && os.Args[1] == "--release-fixture" && os.Args[2] != "" && filepath.IsAbs(os.Args[3]) {
		for {
			time.Sleep(time.Hour)
		}
	}
	if len(os.Args) != 2 {
		os.Exit(2)
	}
	b, e := os.ReadFile(os.Args[1])
	if e != nil {
		os.Exit(3)
	}
	var in evolution.Request
	if json.Unmarshal(b, &in) != nil {
		os.Exit(4)
	}
	if variant == "startup_failure" || variant == "canary_startup_failure" && in.Phase == "CANARY" {
		os.Exit(17)
	}
	if variant == "hang" || variant == "canary_hang" && in.Phase == "CANARY" {
		time.Sleep(10 * time.Second)
		os.Exit(18)
	}
	denied := []bool{}
	if variant == "gate_tamper" {
		for _, path := range in.ProtectedPaths {
			denied = append(denied, os.WriteFile(path, []byte("candidate-forged-authority"), 0600) != nil)
		}
	}
	out := []evolution.Response{}
	for _, c := range in.Cases {
		v := c.A + c.B
		if c.Operation == "multiply" && (variant == "gain" || variant == "regression" || variant == "degrade" || variant == "gate_tamper" || variant == "canary_startup_failure" || variant == "canary_hang") {
			v = c.A * c.B
		}
		if variant == "regression" && c.ID == "negative-input" {
			v = 999
		}
		if variant == "degrade" && in.Phase == "CANARY" && c.ID == "existing-add" {
			v = 999
		}
		score, rubric := 10, "frozen-v1"
		if variant != "stable" {
			score = 100
		}
		if variant == "rubric_only" {
			rubric = "candidate-inflated-v2"
		}
		out = append(out, evolution.Response{ID: c.ID, Value: v, SelfScore: score, Rubric: rubric, WriteDenied: denied})
	}
	if json.NewEncoder(os.Stdout).Encode(out) != nil {
		os.Exit(5)
	}
}
