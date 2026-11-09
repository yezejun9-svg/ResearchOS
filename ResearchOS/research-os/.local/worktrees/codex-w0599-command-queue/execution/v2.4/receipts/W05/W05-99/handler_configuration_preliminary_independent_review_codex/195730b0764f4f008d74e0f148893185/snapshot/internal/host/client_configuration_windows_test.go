//go:build windows

package host

import (
	"context"
	"testing"

	"researchos.local/research-os/internal/domain"
)

func TestConfigurationMetadataActualHostWithoutDecrypt(t *testing.T) {
	h := firstUseHost(t)
	owner, e := h.BootstrapOwner(context.Background())
	if e != nil {
		t.Fatal(e)
	}
	_ = owner // the temporary bootstrap token is never printed.
	p := h.boundPrincipal()
	m, e := h.ConfigurationMetadata(context.Background(), p, "", nil)
	if e != nil || m.OwnerHost != h.InstanceID() || m.Principal != p || h.identity.Kind != "WINDOWS_SID" {
		t.Fatalf("actual local metadata unavailable: %v", e)
	}
	// The intentionally invalid wrapping cannot be decrypted. Metadata reads
	// must succeed without trying to use it, and must never return these bytes.
	ref := "cred-synthetic-metadata"
	record := vaultRecord{Ref: ref, Provider: "fixture-provider", Kind: "API_KEY", Wrapped: []byte("invalid-synthetic-wrapping"), StoredAt: h.nowUTC().Format("2006-01-02T15:04:05Z07:00")}
	if e = writePrivate(h.vault.dir, ref+".dpapi", record); e != nil {
		t.Fatal(e)
	}
	m, e = h.ConfigurationMetadata(context.Background(), p, "fixture-provider", &ref)
	if e != nil || m.Credential == nil || m.Credential.Status != StatusAvailable || m.Credential.Ref != ref {
		t.Fatalf("metadata-only read failed: %v", e)
	}
	if _, e = h.ConfigurationMetadata(context.Background(), p, "foreign-provider", &ref); e == nil {
		t.Fatal("foreign provider accepted")
	}
	if _, e = h.ConfigurationMetadata(context.Background(), "foreign-principal", "fixture-provider", &ref); e == nil {
		t.Fatal("foreign principal accepted")
	}
	record.Revoked = true
	if e = writePrivate(h.vault.dir, ref+".dpapi", record); e != nil {
		t.Fatal(e)
	}
	m, e = h.ConfigurationMetadata(context.Background(), p, "fixture-provider", &ref)
	if e != nil || m.Credential.Status != StatusRevoked {
		t.Fatalf("revocation missing: %v", e)
	}
	if material, err := h.ModelCredential(context.Background(), domain.RuntimeProviderRoute{CredentialRef: ref, CredentialRevision: ref, ModelConfig: domain.Object{"provider": "fixture-provider"}}); err == nil || len(material) != 0 {
		t.Fatal("revoked metadata reached credential dispatch")
	}
	missing := "cred-absent"
	m, e = h.ConfigurationMetadata(context.Background(), p, "fixture-provider", &missing)
	if e != nil || m.Credential.Status != StatusMissing {
		t.Fatalf("absence missing: %v", e)
	}
	old := h.identity.Kind
	h.identity.Kind = "PROCESS_ID"
	if _, e = h.ConfigurationMetadata(context.Background(), p, "", nil); e == nil {
		t.Fatal("PID-only authority accepted")
	}
	h.identity.Kind = old
	state := h.state.HostInstanceID
	h.state.HostInstanceID = "host-foreign"
	if _, e = h.ConfigurationMetadata(context.Background(), p, "", nil); e == nil {
		t.Fatal("different stable instance accepted")
	}
	h.state.HostInstanceID = state
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	if _, e = h.ConfigurationMetadata(ctx, p, "", nil); e == nil {
		t.Fatal("cancel ignored")
	}
	second, err := New(Config{DB: h.db, Dir: h.dir, ContractsDir: "../../spec/v2.0/contracts", MigrationFile: "../../migrations/sqlite/0002_domain.sql", SchemaDir: "../../internal/api/contracts"})
	if err != nil {
		t.Fatal(err)
	}
	metadata, err := second.ConfigurationMetadata(context.Background(), p, "", nil)
	if err != nil || metadata.OwnerHost != m.OwnerHost || second.InstanceID() != h.InstanceID() {
		t.Fatal("same-directory restart changed actual Host identity", err)
	}
}
