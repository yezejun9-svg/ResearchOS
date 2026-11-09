package runtime

import (
	"encoding/json"
	"reflect"
	"strings"
	"testing"
)

func TestCodexRPCProtocolBuilder(t *testing.T) {
	profile := "researchos-readonly-0123456789abcdef0123456789abcdef"
	source := "D:\\source \"quoted\""
	args := codexRPCArguments(profile, source)
	if len(args) < 4 || !reflect.DeepEqual(args[len(args)-3:], []string{"app-server", "--listen", "stdio://"}) {
		t.Fatal("not the one pinned app-server route", args)
	}
	configs := map[string]int{}
	for i := 0; i < len(args)-3; i += 2 {
		if i+1 >= len(args)-3 || args[i] != "-c" {
			t.Fatalf("non-config option before app-server: %v", args)
		}
		configs[args[i+1]]++
	}
	exact := []string{
		`windows.sandbox="mxc"`,
		`default_permissions="` + profile + `"`,
		`permissions.` + profile + `.filesystem={":root"="deny",":minimal"="read",":workspace_roots"={"."="read"}}`,
		`permissions.` + profile + `.network.enabled=false`,
		`approval_policy="never"`, "features.memories=false", "memories.use_memories=false",
	}
	for _, value := range exact {
		if configs[value] != 1 {
			t.Fatalf("required exact policy %q count %d", value, configs[value])
		}
	}
	for key, count := range configs {
		if count != 1 || strings.Contains(key, "=write") || strings.Contains(key, ".windows.sandbox") ||
			strings.Contains(key, "extends") || strings.Contains(key, "CODEX_HOME") {
			t.Fatalf("conflicting policy %q count %d", key, count)
		}
	}
	identity := CodexRPCPolicyIdentity("sha256:" + strings.Repeat("a", 64))
	if identity.PermissionProfile != "researchos-readonly-${PROFILE_NONCE}" || identity.Transport != CodexRPCTransport ||
		identity.HelperContract != CodexRPCHelperContract || identity.RequestedConfigSHA256 == "" {
		t.Fatal("template identity malformed", identity)
	}
	if codexRPCConfigHash(profile, "C:\\owned", source) == identity.RequestedConfigSHA256 ||
		codexRPCConfigHash(profile, "C:\\owned", source) == codexRPCConfigHash(profile+"1", "C:\\owned", source) {
		t.Fatal("rendered config did not bind nonce")
	}
	var turn map[string]any
	if err := json.Unmarshal(rpcTurnStart("thread-1", []byte("payload")), &turn); err != nil {
		t.Fatal(err)
	}
	params, ok := turn["params"].(map[string]any)
	if !ok || len(params) != 2 || params["threadId"] != "thread-1" {
		t.Fatal("turn fields expanded", turn)
	}
	for _, key := range []string{"permissions", "sandboxPolicy", "cwd", "runtimeWorkspaceRoots", "environments", "model", "approvalPolicy", "approvalsReviewer", "collaborationMode"} {
		if _, exists := params[key]; exists {
			t.Fatal("forbidden turn override", key)
		}
	}
	var thread map[string]any
	if err := json.Unmarshal(rpcThreadStart("C:\\owned", source, profile), &thread); err != nil {
		t.Fatal(err)
	}
	threadParams, ok := thread["params"].(map[string]any)
	if !ok {
		t.Fatal("thread params missing")
	}
	if _, selected := threadParams["environments"]; selected {
		t.Fatal("explicit empty environments disables default local route")
	}
}

func TestCodexRPCThreadEvidence(t *testing.T) {
	profile, cwd, source := "researchos-readonly-0123456789abcdef0123456789abcdef", "C:\\owned", "D:\\source"
	makeFrame := func() map[string]any {
		return map[string]any{"id": json.Number("2"), "result": map[string]any{
			"thread":                  map[string]any{"id": "thread-1"},
			"activePermissionProfile": map[string]any{"id": profile},
			"cwd":                     cwd, "runtimeWorkspaceRoots": []any{source}, "approvalPolicy": "never", "approvalsReviewer": "user",
			"sandbox": map[string]any{"type": "readOnly", "networkAccess": false},
		}}
	}
	if id, err := rpcThreadEvidence(makeFrame(), profile, cwd, source); err != nil || id != "thread-1" {
		t.Fatal(id, err)
	}
	for name, mutate := range map[string]func(map[string]any){
		"missing_profile": func(f map[string]any) { delete(f["result"].(map[string]any), "activePermissionProfile") },
		"fallback_profile": func(f map[string]any) {
			f["result"].(map[string]any)["activePermissionProfile"].(map[string]any)["id"] = "default"
		},
		"extends": func(f map[string]any) {
			f["result"].(map[string]any)["activePermissionProfile"].(map[string]any)["extends"] = "base"
		},
		"profile_unknown_grant": func(f map[string]any) {
			f["result"].(map[string]any)["activePermissionProfile"].(map[string]any)["writeAccess"] = true
		},
		"cwd":   func(f map[string]any) { f["result"].(map[string]any)["cwd"] = "C:\\other" },
		"roots": func(f map[string]any) { f["result"].(map[string]any)["runtimeWorkspaceRoots"] = []any{"D:\\other"} },
		"write_sandbox": func(f map[string]any) {
			f["result"].(map[string]any)["sandbox"].(map[string]any)["type"] = "workspaceWrite"
		},
		"network": func(f map[string]any) {
			f["result"].(map[string]any)["sandbox"].(map[string]any)["networkAccess"] = true
		},
		"sandbox_unknown_grant": func(f map[string]any) {
			f["result"].(map[string]any)["sandbox"].(map[string]any)["writableRoots"] = []any{"C:\\private"}
		},
		"approval": func(f map[string]any) { f["result"].(map[string]any)["approvalPolicy"] = "on-request" },
		"reviewer": func(f map[string]any) { f["result"].(map[string]any)["approvalsReviewer"] = "auto" },
		"thread":   func(f map[string]any) { f["result"].(map[string]any)["thread"].(map[string]any)["id"] = "" },
	} {
		t.Run(name, func(t *testing.T) {
			f := makeFrame()
			mutate(f)
			if _, err := rpcThreadEvidence(f, profile, cwd, source); err == nil {
				t.Fatal("mismatch accepted", f)
			}
		})
	}
}

func TestCodexRPCStrictFrames(t *testing.T) {
	for _, raw := range []string{
		"", "startup warning", `{"id":2,"id":2,"result":{}}`,
		`{"id":2,"result":{"sandbox":{"type":"readOnly","type":"workspaceWrite"}}}`,
		`{"jsonrpc":"1.0","id":2}`, `{"id":2}garbage`,
		`{"id":"2","result":{}}`, `{"id":null,"method":"thread/started","params":{}}`,
		`{"id":2,"method":"thread/started","result":{},"params":{}}`,
		`{"id":2,"result":{},"error":{}}`, `{"method":"thread/started","params":{},"result":{}}`,
		"{\"id\":2,\"result\":{\"ignored\":\"" + string([]byte{0xff}) + "\"}}",
	} {
		if _, err := rpcFrame([]byte(raw)); err == nil {
			t.Fatalf("accepted startup corruption: %q", raw)
		}
	}
	if _, err := rpcFrame([]byte(`{"jsonrpc":"2.0","id":2,"result":{}}`)); err != nil {
		t.Fatal(err)
	}
}

func TestCodexRPCUserMessageEnvelope(t *testing.T) {
	input := []byte("{\"schema\":\"researchos.codex-source-context.v1\"}")
	item := map[string]any{"id": "user-1", "type": "userMessage", "content": []any{
		map[string]any{"type": "text", "text": string(input), "text_elements": []any{}}}}
	if !rpcUserMessageMatches(item, input) {
		t.Fatal("official userMessage text with UI text_elements rejected")
	}
	item["content"] = []any{map[string]any{"type": "text", "text": "other"}}
	if rpcUserMessageMatches(item, input) {
		t.Fatal("changed userMessage content accepted")
	}
	item["content"] = []any{}
	if rpcUserMessageMatches(item, input) {
		t.Fatal("missing userMessage content accepted")
	}
}
