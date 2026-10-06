//go:build windows

package domain

import (
	"context"
	"database/sql"
	"testing"
)

func TestHandlerRuntimeStoredProfileExactMapping(t *testing.T) {
	f := contextFixture(t)
	s := &ClientService{Doc: configurationSchema(t), Domain: f.s, ConfigurationAuthority: handlerMetadataFixture{f.owner}}
	credential := "cred-fixture-api_key-1234567890-12345678-12345678"
	env := handlerDefaultEnvelope(1)
	env.Payload = Bytes(Object{"config_revision": 1, "provider_id": "fixture-provider", "base_url": "https://fixture.invalid/v1/", "model_id": "fixture-model", "credential_ref": credential})
	r, _ := handlerCommand(t, f, s, env)
	if deref(r.Status) != "COMPLETED" {
		t.Fatal(string(Bytes(r)))
	}
	ref := Str(r.Result, "model_config_ref")
	config := modelFixtureConfig("https://fixture.invalid/v1/chat/completions")
	config["ref"] = ref
	config["provider"] = "fixture-provider"
	profile := Object{"model_config": config}
	runtime := Object{"id": "runtime-fixture"}
	route := RuntimeProviderRoute{ID: Str(config, "route"), ProjectID: f.project, RuntimeID: "runtime-fixture", Purpose: "mu_turn", Capability: "MODEL", Endpoint: Str(config, "endpoint"), CredentialRef: credential, CredentialRevision: credential, ModelConfig: config}
	c := &RuntimeCoordinator{service: f.s, config: RuntimeCoordinatorConfig{ClientSchema: s.Doc, ConfigurationAuthority: s.ConfigurationAuthority, Providers: []RuntimeProviderRoute{route}}}
	check := func(profile Object) error {
		tx, e := f.db.Begin()
		if e != nil {
			t.Fatal(e)
		}
		defer tx.Rollback()
		return c.matchStoredClientConfiguration(tx, f.project, ref, runtime, profile)
	}
	if e := check(profile); e != nil {
		t.Fatal(e)
	}
	for _, field := range []string{"ref", "api", "provider", "model", "endpoint", "route"} {
		t.Run("profile-"+field, func(t *testing.T) {
			bad := cloneObject(config)
			bad[field] = "different"
			if e := check(Object{"model_config": bad}); e == nil {
				t.Fatal("different profile accepted")
			}
		})
	}
	for _, field := range []string{"credential-ref", "credential-revision", "endpoint", "model-hash", "project", "runtime", "capability"} {
		t.Run("route-"+field, func(t *testing.T) {
			bad := route
			switch field {
			case "credential-ref":
				bad.CredentialRef = "different"
			case "credential-revision":
				bad.CredentialRevision = "different"
			case "endpoint":
				bad.Endpoint = "https://different.invalid"
			case "model-hash":
				bad.ModelConfig = cloneObject(config)
				bad.ModelConfig["model"] = "different"
			case "project":
				bad.ProjectID = "different"
			case "runtime":
				bad.RuntimeID = "different"
			case "capability":
				bad.Capability = "TOOL"
			}
			c.config.Providers = []RuntimeProviderRoute{bad}
			if e := check(profile); e == nil {
				t.Fatal("different route accepted")
			}
			c.config.Providers = []RuntimeProviderRoute{route}
		})
	}
	c.config.ConfigurationAuthority = nil
	if e := check(profile); e == nil {
		t.Fatal("missing authority accepted")
	}
	c.config.ConfigurationAuthority = s.ConfigurationAuthority
	configurationBackupMutation(t, f.db, `DELETE FROM host_model_configurations WHERE model_config_ref=?`, ref)
	if e := check(profile); e == nil {
		t.Fatal("known typed config fell back to legacy after row deletion")
	}
	var effects int
	if e := f.db.QueryRow(`SELECT count(*) FROM resource_effects`).Scan(&effects); e != nil || effects != 0 {
		t.Fatalf("mapping check caused effects=%d %v", effects, e)
	}
}

func cloneObject(in Object) Object { out, _ := Decode(Bytes(in)); return out }

func TestHandlerRuntimeTaskNeedsExactSession(t *testing.T) {
	f := contextFixture(t)
	s, _, _ := handlerTypedSession(t, f, "config-client")
	c := &RuntimeCoordinator{service: f.s, config: RuntimeCoordinatorConfig{ClientSchema: s.Doc, ConfigurationAuthority: s.ConfigurationAuthority}}
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		if e := c.validateTaskSessionConfiguration(context.Background(), tx, f.project, Object{"id": "unassociated"}); e == nil {
			t.Fatal("unassociated task accepted")
		}
		return nil
	})
}
