//go:build windows && researchos_native_recovery_harness

package domain

import "testing"

// Pure matching checks only. Root executes this test independently; it does
// not create fixtures, sign grants, invoke native programs or touch a DB.
func TestNativeHarnessExpectedError(t *testing.T) {
	cases := []struct {
		name     string
		stderr   string
		expected string
		want     bool
	}{
		{"bare-exact", "AUTHORITY_MIGRATION_GRANT", "AUTHORITY_MIGRATION_GRANT", true},
		{"standard-time-prefix", "2026/10/09 05:01:02 AUTHORITY_MIGRATION_GRANT", "AUTHORITY_MIGRATION_GRANT", true},
		{"native-id-collision", "2026/10/09 05:01:02 AUTHORITY_MIGRATION_GRANT_NATIVE_ID", "AUTHORITY_MIGRATION_GRANT", false},
		{"already-used-collision", "2026/10/09 05:01:02 AUTHORITY_MIGRATION_GRANT_ALREADY_USED", "AUTHORITY_MIGRATION_GRANT", false},
		{"size-collision", "2026/10/09 05:01:02 AUTHORITY_MIGRATION_GRANT_SIZE", "AUTHORITY_MIGRATION_GRANT", false},
		{"authority-no-expected", "2026/10/09 05:01:02 AUTHORITY_PRIVATE_INHERITANCE_REQUIRED", "AUTHORITY_MIGRATION_GRANT", false},
		{"expected-prefix-text", "2026/10/09 05:01:02 failure: AUTHORITY_MIGRATION_GRANT", "AUTHORITY_MIGRATION_GRANT", false},
		{"expected-suffix-text", "2026/10/09 05:01:02 AUTHORITY_MIGRATION_GRANT additional detail", "AUTHORITY_MIGRATION_GRANT", false},
		{"unknown-log-prefix", "WARN 2026/10/09 05:01:02 AUTHORITY_MIGRATION_GRANT", "AUTHORITY_MIGRATION_GRANT", false},
		{"invalid-date-prefix", "2026/99/09 05:01:02 AUTHORITY_MIGRATION_GRANT", "AUTHORITY_MIGRATION_GRANT", false},
		{"fractional-prefix-not-current-format", "2026/10/09 05:01:02.123456 AUTHORITY_MIGRATION_GRANT", "AUTHORITY_MIGRATION_GRANT", false},
		{"extra-space-after-time", "2026/10/09 05:01:02  AUTHORITY_MIGRATION_GRANT", "AUTHORITY_MIGRATION_GRANT", false},
		{"control-error-then-root-exit-status", "2026/10/09 05:01:02 AUTHORITY_MIGRATION_GRANT\n2026/10/09 05:01:02 exit status 1\n", "AUTHORITY_MIGRATION_GRANT", true},
		{"first-other-error-not-hidden", "2026/10/09 05:01:02 AUTHORITY_RAW_PIN_MISMATCH\n2026/10/09 05:01:02 AUTHORITY_MIGRATION_GRANT\n", "AUTHORITY_MIGRATION_GRANT", false},
		{"crlf", "2026/10/09 05:01:02 AUTHORITY_MIGRATION_GRANT\r\n2026/10/09 05:01:02 exit status 1\r\n", "AUTHORITY_MIGRATION_GRANT", true},
		{"blank-before-exact", "\n2026/10/09 05:01:02 AUTHORITY_MIGRATION_GRANT\n", "AUTHORITY_MIGRATION_GRANT", true},
		{"no-error", "", "AUTHORITY_MIGRATION_GRANT", false},
		{"empty-expected", "", "", false},
		{"replay-exact", "2026/10/09 05:01:02 AUTHORITY_MIGRATION_GRANT_ALREADY_USED", "AUTHORITY_MIGRATION_GRANT_ALREADY_USED", true},
		{"replay-longer-collision", "2026/10/09 05:01:02 AUTHORITY_MIGRATION_GRANT_ALREADY_USED_EXTRA", "AUTHORITY_MIGRATION_GRANT_ALREADY_USED", false},
		{"wrong-owner-complete", "2026/10/09 05:01:02 FORBIDDEN: current project Owner required", "FORBIDDEN: current project Owner required", true},
		{"wrong-owner-missing-fault-code", "2026/10/09 05:01:02 current project Owner required", "FORBIDDEN: current project Owner required", false},
		{"lease-full-localized-message", "2026/10/09 05:01:02 示例租约错误（仅匹配测试）", "示例租约错误（仅匹配测试）", true},
		{"lease-extra-prefix", "2026/10/09 05:01:02 detail: 示例租约错误（仅匹配测试）", "示例租约错误（仅匹配测试）", false},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			if got := nativeHarnessExpectedError([]byte(tc.stderr), tc.expected); got != tc.want {
				t.Fatalf("match=%v want=%v stderr=%q expected=%q", got, tc.want, tc.stderr, tc.expected)
			}
		})
	}
}
