package recoveryauthority

import (
	"crypto/ed25519"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"reflect"
	"strings"
	"testing"
	"time"
)

func testAdoption(t *testing.T) (Adoption, Release, Grant, []byte, ed25519.PrivateKey) {
	t.Helper()
	pub, key, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		t.Fatal(err)
	}
	now := time.Now().UTC()
	expired := now.Add(-time.Hour)
	start := expired.Add(-300 * time.Second)
	tuple := Tuple{ProjectID: "p", TaskID: "t", RunID: "r", RuntimeID: "runtime", OwnerRoot: "owner", Epoch: 1, RunRevision: 1, TaskRevision: 2, DispatchKey: "dispatch", ManifestHash: digest([]byte("manifest"))}
	g := Grant{Tuple: tuple, Root: "root", RootIdentity: "root-id", Database: "db", DatabaseIdentity: "db-id", Nonce: strings.Repeat("ab", 32), ExpiresUTC: now.Add(time.Minute).Format(time.RFC3339Nano)}
	raw := encoded(g)
	r := Release{ID: "release", RootSigningPublicKey: hex.EncodeToString(pub)}
	a := Adoption{Schema: Schema, Kind: "HISTORICAL_EVIDENCE_ADOPTION", Purpose: Purpose, ReleaseID: r.ID, GrantSHA256: digest(raw), Tuple: tuple, Root: g.Root, RootIdentity: g.RootIdentity, Database: g.Database, DatabaseIdentity: g.DatabaseIdentity, Nonce: g.Nonce, ExpiresUTC: g.ExpiresUTC, SignedUTC: now.Format(time.RFC3339Nano), RootStartedUTC: start.Format(time.RFC3339Nano), RootClockExpiredUTC: expired.Format(time.RFC3339Nano), StateVerification: "REQUIRE_CURRENT_OWNER_AND_EXACT_CAS", Historical: HistoricalObserver{OwnerPID: 1, HostPID: 2, HostBirth100ns: "134359521876434319", HostJobID: "old-job", RunUUID: "old-run", ClosedObservedMonotonic: "338455.6112153"}, Producer: ProcessIdentity{PID: 3, Birth100ns: "134360000000000001"}}
	a.Maintenance = ProcessIdentity{PID: 4, Birth100ns: "134360000000000002"}
	a.Signature = hex.EncodeToString(ed25519.Sign(key, append([]byte(Purpose+"/adoption\x00"), encoded(a)...)))
	return a, r, g, raw, key
}
func TestAuthorityHistoricalAdoptionCurrentSignatureAndNulls(t *testing.T) {
	a, r, g, raw, _ := testAdoption(t)
	if err := verifyAdoption(a, r, g, raw); err != nil {
		t.Fatal(err)
	}
	cases := map[string]func(*Adoption){
		"forged old signature":      func(v *Adoption) { s := "invented"; v.Historical.OriginalRootSignature = &s },
		"invented absolute closure": func(v *Adoption) { s := time.Now().UTC().Format(time.RFC3339Nano); v.Historical.ExactJobClosedUTC = &s },
		"unknown converted to zero": func(v *Adoption) { n := int64(0); v.ProviderRequests = &n },
		"closed accounting":         func(v *Adoption) { v.FinancialClosed = true },
		"different tuple":           func(v *Adoption) { v.Tuple.RunID = "other" },
		"different exact birth":     func(v *Adoption) { v.Historical.HostBirth100ns = "134359521876434320" },
		"expired current signature": func(v *Adoption) { v.ExpiresUTC = time.Now().Add(-time.Second).UTC().Format(time.RFC3339Nano) },
		"wrong protocol":            func(v *Adoption) { v.Purpose = MigrationPurpose },
	}
	for name, mutate := range cases {
		t.Run(name, func(t *testing.T) {
			v := a
			mutate(&v)
			if verifyAdoption(v, r, g, raw) == nil {
				t.Fatal("modified adoption accepted")
			}
		})
	}
	b := encoded(a)
	if !strings.Contains(string(b), `"host_birth_100ns":"134359521876434319"`) || !strings.Contains(string(b), `"exact_job_closed_utc":null`) || !strings.Contains(string(b), `"original_root_signature":null`) {
		t.Fatal("lossless identities/null facts lost")
	}
}
func TestAuthorityOpaqueZeroAndJSONCannotMint(t *testing.T) {
	var token Token
	var migration MigrationToken
	if err := json.Unmarshal([]byte(`{"state":{"phase":"READY","approved":true}}`), &token); err != nil {
		t.Fatal(err)
	}
	if token.Check("root", "db", digest(nil)) == nil || token.Begin(digest(nil)) == nil {
		t.Fatal("JSON minted authority")
	}
	if err := json.Unmarshal([]byte(`{"state":{"phase":"READY"}}`), &migration); err != nil {
		t.Fatal(err)
	}
	if migration.Check(MigrationBinding{}) == nil || migration.Begin(MigrationBinding{}) == nil {
		t.Fatal("JSON minted migration authority")
	}
	for _, typ := range []reflect.Type{reflect.TypeOf(token), reflect.TypeOf(migration)} {
		for i := 0; i < typ.NumField(); i++ {
			if typ.Field(i).IsExported() {
				t.Fatal("exported capability state")
			}
		}
	}
}
func TestAuthorityAdoptionSignatureCannotServeAsMigrationGrant(t *testing.T) {
	a, _, _, _, _ := testAdoption(t)
	if _, err := verifyMigrationGrant(encoded(a), nil); err == nil {
		t.Fatal("adoption upgraded to schema authority")
	}
	b := MigrationBinding{PlanID: MigrationPlanID, OwnerRoot: "owner", ProjectID: "project", Root: "root", RootIdentity: "root-id", Database: "db", DatabaseIdentity: "db-id", SQLSHA256: digest([]byte("unreviewed SQL"))}
	if validMigrationBinding(b) == nil {
		t.Fatal("unreviewed DDL accepted")
	}
}
func TestAuthorityPinCoverageRejectsMissingDuplicateAndBadDigest(t *testing.T) {
	pins := []RawPin{}
	for _, role := range requiredHistoryRoles {
		pins = append(pins, RawPin{Role: role, Path: role, SHA256: digest([]byte(role)), Bytes: 1})
	}
	if err := validatePinRoles(pins); err != nil {
		t.Fatal(err)
	}
	if validatePinRoles(pins[1:]) == nil {
		t.Fatal("omitted raw evidence accepted")
	}
	if validatePinRoles(append(append([]RawPin(nil), pins...), pins[0])) == nil {
		t.Fatal("duplicate role accepted")
	}
	pins[0].SHA256 = "approved"
	if validatePinRoles(pins) == nil {
		t.Fatal("text trusted as digest")
	}
}
