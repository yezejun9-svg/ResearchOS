//go:build windows

package domain

import (
	"context"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
)

func upgradeJunction(t *testing.T, target string) string {
	t.Helper()
	alias := filepath.Join(t.TempDir(), "junction")
	output, e := exec.Command("cmd.exe", "/c", "mklink", "/J", alias, target).CombinedOutput()
	if e != nil {
		t.Fatalf("native junction fixture: %v %s", e, output)
	}
	// Remove only this link, before TempDir cleanup; never recurse its target.
	t.Cleanup(func() {
		if e := os.Remove(alias); e != nil && !os.IsNotExist(e) {
			t.Error(e)
		}
	})
	return alias
}

func TestW17UpgradeNativeJunctionOverlap(t *testing.T) {
	for _, scenario := range []string{"snapshot-source", "target-key", "source-alias", "nested-junction", "outputs-overlap"} {
		t.Run(scenario, func(t *testing.T) {
			opt, f, fake := upgradeFixture(t, true)
			f.db.Close()
			switch scenario {
			case "snapshot-source":
				opt.Snapshot = filepath.Join(upgradeJunction(t, filepath.Dir(opt.Source)), "new", "snapshot")
			case "target-key":
				opt.Destination = filepath.Join(upgradeJunction(t, filepath.Dir(opt.KeyFile)), "new", "target")
			case "source-alias":
				original := filepath.Dir(opt.Source)
				opt.Source = filepath.Join(upgradeJunction(t, original), filepath.Base(opt.Source))
				opt.Snapshot = filepath.Join(original, "new", "snapshot")
			case "nested-junction":
				opt.Snapshot = filepath.Join(upgradeJunction(t, upgradeJunction(t, filepath.Dir(opt.Source))), "snapshot")
			case "outputs-overlap":
				base := t.TempDir()
				opt.Snapshot = filepath.Join(base, "output")
				opt.Destination = filepath.Join(upgradeJunction(t, base), "output", "target")
			}
			_, e := upgradeLocal(context.Background(), opt, fake.verifier())
			if e == nil || !strings.Contains(e.Error(), "UPGRADE_PATH_OVERLAP") {
				t.Fatalf("junction separation escaped: %v", e)
			}
			for _, output := range []string{opt.Snapshot, opt.Destination} {
				if _, e := os.Stat(output); !os.IsNotExist(e) {
					t.Fatalf("rejected output created: %s: %v", output, e)
				}
			}
			upgradeAssert(t, "JUNCTION-REJECT-"+scenario, []int{0, 0}, []int{fake.refreshes, fake.reads})
		})
	}
}

func TestW17UpgradeNativeJunctionDisjoint(t *testing.T) {
	opt, f, fake := upgradeFixture(t, true)
	f.db.Close()
	base := t.TempDir()
	alias := upgradeJunction(t, base)
	opt.Destination = filepath.Join(alias, "new", "target")
	_, e := upgradeLocal(context.Background(), opt, fake.verifier())
	if e != nil {
		t.Fatal(e)
	}
	if _, e = os.Stat(filepath.Join(base, "new", "target", "researchos.sqlite")); e != nil {
		t.Fatal(e)
	}
	upgradeAssert(t, "JUNCTION-DISJOINT-PUBLISHED-CANONICAL-TARGET", 0, fake.reads)
}
