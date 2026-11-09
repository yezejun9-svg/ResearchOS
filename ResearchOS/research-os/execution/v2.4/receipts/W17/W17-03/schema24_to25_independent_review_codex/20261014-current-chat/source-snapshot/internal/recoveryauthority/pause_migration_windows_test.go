//go:build windows

package recoveryauthority

import (
	"bytes"
	"context"
	"testing"
)

func TestPauseMigrationNativeRequiresInheritanceAndOwnTransport(t *testing.T) {
	t.Setenv(bootstrapEnv, "")
	if _, _, err := ReceivePauseMigrationInherited(context.Background()); err == nil {
		t.Fatal("public invocation minted pause token")
	}
	key := bytes.Repeat([]byte{1}, 32)
	for _, purpose := range []string{Purpose, MigrationPurpose, PauseMigrationPurpose} {
		var buf bytes.Buffer
		if err := writeFrame(&buf, key, purpose, map[string]string{"fixture": "transport only"}); err != nil {
			t.Fatal(err)
		}
		for _, receiver := range []string{Purpose, MigrationPurpose, PauseMigrationPurpose} {
			var out map[string]string
			err := readFrame(bytes.NewReader(buf.Bytes()), key, receiver, &out)
			if (err == nil) != (purpose == receiver) {
				t.Fatal("transport purpose boundary", purpose, receiver, err)
			}
		}
	}
}
