package recoveryauthority

import (
	"encoding/json"
	"strings"
	"testing"
	"time"
)

func pauseTestGrant(spec migrationDescriptor) MigrationGrant {
	now := time.Now().UTC()
	pin := func(role string) RawPin {
		return RawPin{Role: role, Path: role, SHA256: digest([]byte(role)), Bytes: 1}
	}
	g := MigrationGrant{Schema: spec.schema, Purpose: spec.purpose, Stage: "APPLY_ORIGINAL", ReleaseSHA256: digest([]byte("release")), Nonce: strings.Repeat("12", 32), IssuedUTC: now.Add(-time.Second).Format(time.RFC3339Nano), ExpiresUTC: now.Add(time.Minute).Format(time.RFC3339Nano), Options: json.RawMessage(`{}`)}
	g.Binding = MigrationBinding{PlanID: spec.plan, OwnerRoot: "owner", ProjectID: "p", Root: "root", RootIdentity: "root-id", Database: "db", DatabaseIdentity: "db-id", SourceReleaseSHA256: digest([]byte("source-program")), TargetReleaseSHA256: digest([]byte("target-program")), SourceInventorySHA256: digest(nil), TargetInventorySHA256: digest(nil), SourceSchemaSHA256: digest(nil), TargetSchemaSHA256: digest(nil), SQLSHA256: spec.sql, OriginalRowsSHA256: digest(nil), OptionsSHA256: digest(g.Options), Backup: pin("encrypted-backup-manifest"), Rehearsal: pin("isolated-restore-rehearsal")}
	for _, role := range []string{"source-program", "target-program", "migration-sql", "encrypted-backup-manifest", "isolated-restore-rehearsal"} {
		p := pin(role)
		if role == "migration-sql" {
			p.SHA256 = spec.sql
		}
		g.Pins = append(g.Pins, p)
	}
	for _, role := range spec.extraRoles {
		g.Pins = append(g.Pins, pin(role))
	}
	return g
}

// This validates public payload structure; it deliberately cannot mint a token
// or substitute for verification under the enrolled issuer public key.
func TestPauseMigrationGrantFieldsAndCrossPurpose(t *testing.T) {
	for _, spec := range []migrationDescriptor{preparedMigrationDescriptor, pauseMigrationDescriptor} {
		if err := validateMigrationGrantFields(pauseTestGrant(spec), spec); err != nil {
			t.Fatal(err)
		}
	}
	if validateMigrationGrantFields(pauseTestGrant(preparedMigrationDescriptor), pauseMigrationDescriptor) == nil || validateMigrationGrantFields(pauseTestGrant(pauseMigrationDescriptor), preparedMigrationDescriptor) == nil {
		t.Fatal("cross-purpose payload accepted")
	}
	for _, mutation := range []string{"purpose", "schema", "plan", "sql", "stage", "expired", "future", "long-life", "nonce", "release", "options", "missing-pin", "duplicate-pin", "bad-pin-hash", "wrong-program-pin", "backup-pin", "receipt-pin"} {
		t.Run(mutation, func(t *testing.T) {
			g := pauseTestGrant(pauseMigrationDescriptor)
			switch mutation {
			case "purpose":
				g.Purpose = Purpose
			case "schema":
				g.Schema = preparedMigrationDescriptor.schema
			case "plan":
				g.Binding.PlanID = MigrationPlanID
			case "sql":
				g.Binding.SQLSHA256 = MigrationSQLSHA256
			case "stage":
				g.Stage = "REHEARSAL"
			case "expired":
				g.ExpiresUTC = time.Now().Add(-time.Second).UTC().Format(time.RFC3339Nano)
			case "future":
				g.IssuedUTC = time.Now().Add(time.Hour).UTC().Format(time.RFC3339Nano)
			case "long-life":
				g.ExpiresUTC = time.Now().Add(time.Hour).UTC().Format(time.RFC3339Nano)
			case "nonce":
				g.Nonce = "12"
			case "release":
				g.ReleaseSHA256 = "approved"
			case "options":
				g.Options = json.RawMessage(`{"changed":true}`)
			case "missing-pin":
				g.Pins = g.Pins[:len(g.Pins)-1]
			case "duplicate-pin":
				g.Pins = append(g.Pins, g.Pins[0])
			case "bad-pin-hash":
				g.Pins[0].SHA256 = "approved"
			case "wrong-program-pin":
				g.Pins[0].SHA256 = digest(nil)
			case "backup-pin":
				g.Binding.Backup.Path = "other"
			case "receipt-pin":
				g.Binding.Rehearsal.Bytes++
			}
			if validateMigrationGrantFields(g, pauseMigrationDescriptor) == nil {
				t.Fatal("invalid grant accepted", mutation)
			}
		})
	}
	for _, raw := range [][]byte{encoded(pauseTestGrant(pauseMigrationDescriptor)), encoded(pauseTestGrant(preparedMigrationDescriptor)), []byte(`{"signature":"00","payload":{}}`)} {
		if _, err := verifyPauseMigrationGrant(raw, []byte("release")); err == nil {
			t.Fatal("unsigned public fields minted grant")
		}
	}
	a, _, _, _, _ := testAdoption(t)
	if _, err := verifyPauseMigrationGrant(encoded(a), nil); err == nil {
		t.Fatal("adoption accepted as pause grant")
	}
}

func TestPauseMigrationEachAdditionalEvidencePinRequired(t *testing.T) {
	for _, role := range pauseMigrationDescriptor.extraRoles {
		t.Run(role, func(t *testing.T) {
			g := pauseTestGrant(pauseMigrationDescriptor)
			pins := []RawPin{}
			for _, p := range g.Pins {
				if p.Role != role {
					pins = append(pins, p)
				}
			}
			g.Pins = pins
			if validateMigrationGrantFields(g, pauseMigrationDescriptor) == nil {
				t.Fatal("omitted evidence accepted")
			}
		})
	}
}
