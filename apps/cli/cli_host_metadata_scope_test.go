package main

import (
	"reflect"
	"testing"
)

func hostMetadataTestContext() *v2Context {
	return &v2Context{
		clientID: "metadata-client", credential: "fixture-credential",
		projectID: "11111111111111111111111111111111",
		sessionID: "22222222222222222222222222222222",
		revision:  7, epoch: 3, commandID: "metadata-command",
	}
}

func TestCLIHostMetadataReadScope(t *testing.T) {
	for _, method := range []string{"host.status", "workspace.list"} {
		t.Run(method, func(t *testing.T) {
			ctx := hostMetadataTestContext()
			before := *ctx
			env, refusal := v2EnvelopeFor(ctx, method, map[string]any{})
			if refusal != "" || env == nil {
				t.Fatalf("envelope refusal: %s", refusal)
			}
			if env.ClientID != ctx.clientID || env.ProjectID == nil || *env.ProjectID != ctx.projectID ||
				env.SessionID != nil || env.ExpectedRevision != nil || env.WriterEpoch != nil {
				t.Fatalf("%s carried session or writer state: %+v", method, env)
			}
			if !reflect.DeepEqual(*ctx, before) {
				t.Fatal("metadata read mutated selected context")
			}
		})
	}
}

func TestCLIHostMetadataSessionControls(t *testing.T) {
	ctx := hostMetadataTestContext()
	before := *ctx
	get, refusal := v2EnvelopeFor(ctx, "session.get", map[string]any{})
	if refusal != "" || get.SessionID == nil || *get.SessionID != ctx.sessionID ||
		get.ProjectID == nil || *get.ProjectID != ctx.projectID ||
		get.ExpectedRevision != nil || get.WriterEpoch != nil {
		t.Fatalf("session.get scope changed: %s %+v", refusal, get)
	}
	attach, refusal := v2EnvelopeFor(ctx, "session.attach", map[string]any{
		"after_sequence": 0, "request_write_owner": false,
	})
	if refusal != "" || attach.SessionID == nil || attach.WriterEpoch == nil || *attach.WriterEpoch != ctx.epoch {
		t.Fatalf("session.attach scope changed: %s %+v", refusal, attach)
	}
	send, refusal := v2EnvelopeFor(ctx, "session.send", map[string]any{
		"text": "fixture", "attachment_artifact_ids": []string{}, "delivery": "immediate",
	})
	if refusal != "" || send.SessionID == nil || send.ExpectedRevision == nil ||
		*send.ExpectedRevision != ctx.revision || send.WriterEpoch == nil || *send.WriterEpoch != ctx.epoch {
		t.Fatalf("session.send scope changed: %s %+v", refusal, send)
	}
	configure, refusal := v2EnvelopeFor(ctx, "host.configure", map[string]any{
		"config_revision": 1, "provider_id": "openai", "base_url": "http://127.0.0.1",
		"model_id": "fixture", "credential_ref": "fixture-ref",
	})
	if refusal != "" || configure.SessionID == nil || *configure.SessionID != ctx.sessionID ||
		configure.ExpectedRevision == nil || *configure.ExpectedRevision != ctx.revision ||
		configure.WriterEpoch == nil || *configure.WriterEpoch != ctx.epoch {
		t.Fatalf("host.configure scope changed: %s %+v", refusal, configure)
	}
	if !reflect.DeepEqual(*ctx, before) {
		t.Fatal("session controls mutated selected context")
	}
}
