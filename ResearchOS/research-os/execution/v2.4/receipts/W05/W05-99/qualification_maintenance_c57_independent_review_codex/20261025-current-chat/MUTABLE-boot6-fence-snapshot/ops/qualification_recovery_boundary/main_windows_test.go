//go:build windows

package main

import (
	"context"
	"strings"
	"testing"
)

func TestCLIOnlyFixedPhasesAndExactSelector(t *testing.T) {
	sha := strings.Repeat("a", 64)
	for _, args := range [][]string{
		nil, {"server"}, {"arm", "--data-root", "C:\\fixture", "--operation-id", "0123456789abcdef0123456789abcdef", "--plan-sha256", sha, "--sql", "delete"},
		{"arm", "--data-root", "C:\\fixture", "--operation-id", "0123456789abcdef0123456789abcdef"},
		{"status", "--data-root", "C:\\fixture", "--operation-id", "0123456789abcdef0123456789abcdef", "--plan-sha256", sha, "extra"},
	} {
		if _, _, _, _, err := parse(args); err == nil {
			t.Fatalf("invalid selector accepted: %q", args)
		}
	}
	phase, root, operation, plan, err := parse([]string{"status", "--data-root", "C:\\fixture", "--operation-id", "0123456789abcdef0123456789abcdef", "--plan-sha256", sha})
	if err != nil || phase != "status" || root != "C:\\fixture" || operation != "0123456789abcdef0123456789abcdef" || plan != sha {
		t.Fatalf("fixed status parse: %q %q %q %q %v", phase, root, operation, plan, err)
	}
	if _, err := run(context.Background(), []string{"plan", "--data-root", "relative", "--operation-id", "0123456789abcdef0123456789abcdef", "--plan-sha256", sha}); err == nil {
		t.Fatal("relative root reached helper")
	}
}
