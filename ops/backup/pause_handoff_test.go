package main

import (
	"os"
	"strings"
	"testing"
)

func TestPauseHandoffCommandIsSeparateAndRequiresExactPlan(t *testing.T) {
	old := os.Args
	defer func() { os.Args = old }()
	for _, command := range []string{"upgrade-pause-backup", "upgrade-local"} {
		os.Args = []string{"backup", command, "--key-file", "absent", "--out", "absent", "--plan", "schema24-to25-runtime-pause-v1"}
		err := run()
		if err == nil {
			t.Fatal("incomplete public arguments accepted")
		}
		if strings.Contains(err.Error(), "unknown command") {
			t.Fatal("new command missing", err)
		}
		if command == "upgrade-local" && !strings.Contains(err.Error(), "UPGRADE_PLAN_UNSUPPORTED") {
			t.Fatal("new plan entered old local route", err)
		}
	}
}
