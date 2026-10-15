//go:build windows

package main

import (
	"os"
	"strings"
	"testing"
)

func TestPauseRootAcceptsOnlyFixedPurposeAndPrivateInput(t *testing.T) {
	oldArgs, oldInput := os.Args, os.Stdin
	defer func() { os.Args, os.Stdin = oldArgs, oldInput }()
	for _, args := range [][]string{{"root", "schema24-to25"}, {"root", "schema24-to25", "--grant", "caller.json"}, {"root", "arbitrary-purpose"}} {
		r, w, err := os.Pipe()
		if err != nil {
			t.Fatal(err)
		}
		if _, err = w.WriteString("fixture-owner-no-authority"); err != nil {
			t.Fatal(err)
		}
		w.Close()
		os.Args, os.Stdin = args, r
		err = run()
		r.Close()
		if err == nil {
			t.Fatal("un-enrolled root accepted", args)
		}
		if len(args) != 2 || args[1] != "schema24-to25" {
			if !strings.Contains(err.Error(), "fixed recovery purpose") {
				t.Fatal("caller chose authority path", err)
			}
		}
	}
}
