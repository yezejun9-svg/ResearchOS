package domain

import (
	"strings"
	"testing"
)

func TestHarnessV1Validation(t *testing.T) {
	for _, v := range []string{"", "00", "+1", "-1", "1.0", "9223372036854775808", " 1"} {
		t.Run("decimal-"+v, func(t *testing.T) {
			if _, err := HarnessDecimal(v, false); err == nil {
				t.Fatal("noncanonical decimal accepted")
			}
		})
	}
	if n, err := HarnessDecimal("9007199254740993", true); err != nil || n != 9007199254740993 {
		t.Fatal(n, err)
	}
	valid := HarnessSubmit{RequestID: "safe:1", ProjectID: "p", WorkspaceRef: "opaque-w", HarnessID: "codex", Scope: "workspace-read", Prompt: "bounded task"}
	if err := valid.Validate(); err != nil {
		t.Fatal(err)
	}
	for _, v := range []string{"", " \r\n", string([]byte{0xff}), strings.Repeat("x", 65537)} {
		copy := valid
		copy.Prompt = v
		if copy.Validate() == nil {
			t.Fatal("invalid prompt accepted")
		}
	}
	run := "r"
	epoch := "1"
	cancel := HarnessCancel{RequestID: "cancel", ExpectedTaskRevision: "1", ExpectedRunID: &run}
	if cancel.Validate() == nil {
		t.Fatal("half-null fence accepted")
	}
	cancel.ExpectedEpoch = &epoch
	if err := cancel.Validate(); err != nil {
		t.Fatal(err)
	}
}
