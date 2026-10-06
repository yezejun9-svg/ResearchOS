package main

import (
	"encoding/json"
	"strings"
	"testing"
)

func TestOracleRejectsLivenessAndMalformedMachineOutput(t *testing.T) {
	for name, raw := range map[string]string{
		"liveness only":          `{"command":"doctor","status":"COMPLETED","exit_code":0,"health":"UP"}`,
		"banner":                 "hello\n{\"command\":\"doctor\"}",
		"two records":            "{}\n{}",
		"trailing second object": "{} {}",
		"null":                   "null",
		"array":                  "[]",
	} {
		t.Run(name, func(t *testing.T) {
			value, err := parseReport([]byte(raw))
			c := observation{Report: value, Exit: 0}
			if err != nil {
				c.ParseError = err.Error()
			}
			if validLayers(c) {
				t.Fatal("weak or malformed report passed")
			}
		})
	}
}

func TestOracleLayerContractHasPositiveAndMutationControls(t *testing.T) {
	makeReport := func() observation {
		layers := object{}
		for _, name := range layerNames {
			layers[name] = object{"status": "NOT_CHECKED", "reason": "no independent witness"}
		}
		raw, _ := json.Marshal(object{"command": "doctor", "status": "COMPLETED", "exit_code": 0, "layers": layers})
		report, err := parseReport(raw)
		if err != nil {
			t.Fatal(err)
		}
		return observation{Report: report, Exit: 0}
	}
	if !validLayers(makeReport()) {
		t.Fatal("valid shape control refused")
	}
	mutants := map[string]func(*observation){
		"missing layer": func(c *observation) { delete(c.Report["layers"].(map[string]any), "inference") },
		"unknown status": func(c *observation) {
			c.Report["layers"].(map[string]any)["inference"].(map[string]any)["status"] = "OK"
		},
		"empty reason":  func(c *observation) { c.Report["layers"].(map[string]any)["tool"].(map[string]any)["reason"] = "  " },
		"invented exit": func(c *observation) { c.Exit = 1 },
		"timeout":       func(c *observation) { c.TimedOut = true },
		"overflow":      func(c *observation) { c.Overflow = true },
	}
	for name, mutate := range mutants {
		t.Run(name, func(t *testing.T) {
			c := makeReport()
			mutate(&c)
			if validLayers(c) {
				t.Fatal("mutant passed")
			}
		})
	}
}

func TestOracleOutputIsBoundedWithoutStoppingPipeDrain(t *testing.T) {
	var b boundedBuffer
	input := []byte(strings.Repeat("x", (1<<20)+23))
	n, err := b.Write(input)
	if err != nil || n != len(input) || b.Len() != 1<<20 || !b.overflow {
		t.Fatal("output limit or pipe-drain contract broken")
	}
	n, err = b.Write([]byte("still draining"))
	if n != len("still draining") || err != nil || b.Len() != 1<<20 {
		t.Fatal("overflow stopped draining")
	}
}
