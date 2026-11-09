package domain

import (
	"os"
	"os/exec"
	"strings"
	"testing"
)

func TestS1UpgradeProjectionReview(t *testing.T) {
	if os.Getenv("S1_REVIEW_NONEMPTY") == "1" {
		f := setup(t)
		if _, err := f.db.Exec("CREATE TABLE review_post13_sentinel(value TEXT); INSERT INTO review_post13_sentinel VALUES ('must not disappear')"); err != nil {
			t.Fatal(err)
		}
		upgradeCopyFixture13(t, f, upgradeTestRelease(t, 13))
		t.Fatal("nonempty post13 table was silently discarded")
	}
	t.Run("pristine13", func(t *testing.T) {
		_, f, _ := upgradeFixture(t, false)
		var maxVersion, count, runtimeTables int
		if err := f.db.QueryRow("SELECT MAX(version), COUNT(*) FROM schema_migrations").Scan(&maxVersion, &count); err != nil {
			t.Fatal(err)
		}
		if err := f.db.QueryRow("SELECT COUNT(*) FROM sqlite_master WHERE name='runtime_qualification_runs'").Scan(&runtimeTables); err != nil {
			t.Fatal(err)
		}
		if maxVersion != 13 || count != 13 || runtimeTables != 0 {
			t.Fatalf("projection changed baseline: max=%d count=%d runtimeTables=%d", maxVersion, count, runtimeTables)
		}
	})
	t.Run("nonempty-new-table-rejected", func(t *testing.T) {
		program, err := os.Executable()
		if err != nil {
			t.Fatal(err)
		}
		cmd := exec.Command(program, "-test.run=^TestS1UpgradeProjectionReview$", "-test.v")
		cmd.Env = append(os.Environ(), "S1_REVIEW_NONEMPTY=1")
		raw, err := cmd.CombinedOutput()
		t.Log(string(raw))
		if err == nil || !strings.Contains(string(raw), "newer fixture table review_post13_sentinel is not empty; cannot project into schema13") {
			t.Fatalf("expected bounded refusal, got %v: %s", err, raw)
		}
	})
}
