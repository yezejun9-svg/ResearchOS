package runtime

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"strconv"
	"strings"
)

const (
	rpcCaptureLimit       = 8 << 20
	rpcFrameLimit         = 1 << 20
	rpcPreparationSeconds = 45
)

func codexRPCArguments(profile, source string) []string {
	q := strconv.Quote
	return []string{
		"-c", "default_permissions=" + q(profile),
		"-c", `windows.sandbox="mxc"`,
		"-c", "permissions." + profile + `.filesystem={":root"="deny",":minimal"="read",":workspace_roots"={"."="read"}}`,
		"-c", "permissions." + profile + ".workspace_roots={" + q(source) + "=true}",
		"-c", "permissions." + profile + ".network.enabled=false",
		"-c", `approval_policy="never"`,
		"-c", "features.memories=false", "-c", "memories.use_memories=false",
		"-c", "features.hooks=false", "-c", "features.plugins=false", "-c", "features.remote_plugin=false",
		"-c", "features.skill_mcp_dependency_install=false", "-c", "features.apps=false",
		"-c", "notify=[]", "-c", `web_search="disabled"`,
		"-c", `project_root_markers=[".researchos-codex-root"]`,
		"app-server", "--listen", "stdio://",
	}
}

func codexRPCThreadStart(cwd, source, profile string) map[string]any {
	return map[string]any{
		"cwd": cwd, "runtimeWorkspaceRoots": []string{source}, "permissions": profile,
		"approvalPolicy": "never", "approvalsReviewer": "user", "ephemeral": true,
		"environments": []any{},
	}
}

func codexRPCConfigHash(profile, cwd, source string) string {
	raw, _ := json.Marshal(struct {
		Args   []string
		Thread map[string]any
	}{
		codexRPCArguments(profile, source), codexRPCThreadStart(cwd, source, profile),
	})
	sum := sha256.Sum256(raw)
	return "sha256:" + hex.EncodeToString(sum[:])
}

func CodexRPCPolicyIdentity(binarySHA256 string) CodexPolicyIdentity {
	return CodexPolicyIdentity{
		Revision: CodexRPCPolicyRevision, WindowsSandbox: CodexWindowsSandbox,
		PermissionProfile:     "researchos-readonly-${PROFILE_NONCE}",
		RequestedConfigSHA256: codexRPCConfigHash("researchos-readonly-${PROFILE_NONCE}", "${OWNED_CWD}", "${SOURCE_ROOT}"),
		BinarySHA256:          binarySHA256, Transport: CodexRPCTransport, HelperContract: CodexRPCHelperContract,
	}
}

func rpcRequest(id int, method string, params any) []byte {
	raw, _ := json.Marshal(map[string]any{"id": id, "method": method, "params": params})
	return append(raw, '\n')
}
func rpcInitialized() []byte { return []byte("{\"method\":\"initialized\",\"params\":{}}\n") }
func rpcInitialize() []byte {
	return rpcRequest(1, "initialize", map[string]any{
		"clientInfo":   map[string]string{"name": "researchos", "title": "ResearchOS", "version": "1"},
		"capabilities": map[string]any{"experimentalApi": true},
	})
}
func rpcThreadStart(cwd, source, profile string) []byte {
	return rpcRequest(2, "thread/start", codexRPCThreadStart(cwd, source, profile))
}
func rpcTurnStart(threadID string, input []byte) []byte {
	return rpcRequest(3, "turn/start", map[string]any{
		"threadId": threadID,
		"input":    []any{map[string]any{"type": "text", "text": string(input)}},
	})
}

// Decode duplicate-free JSON. Go's ordinary map unmarshal accepts duplicate
// keys, which would make a response's effective policy ambiguous.
func rpcDecodeUnique(raw []byte) (map[string]any, error) {
	d := json.NewDecoder(bytes.NewReader(raw))
	d.UseNumber()
	value, err := rpcValue(d)
	if err != nil {
		return nil, err
	}
	if _, err = d.Token(); err != io.EOF {
		return nil, errors.New("CODEX_RPC_TRAILING_JSON")
	}
	object, ok := value.(map[string]any)
	if !ok {
		return nil, errors.New("CODEX_RPC_OBJECT_REQUIRED")
	}
	return object, nil
}
func rpcValue(d *json.Decoder) (any, error) {
	token, err := d.Token()
	if err != nil {
		return nil, err
	}
	delim, ok := token.(json.Delim)
	if !ok {
		return token, nil
	}
	switch delim {
	case '{':
		value := map[string]any{}
		for d.More() {
			keyToken, err := d.Token()
			if err != nil {
				return nil, err
			}
			key, ok := keyToken.(string)
			if !ok {
				return nil, errors.New("CODEX_RPC_KEY_INVALID")
			}
			if _, found := value[key]; found {
				return nil, errors.New("CODEX_RPC_DUPLICATE_KEY")
			}
			item, err := rpcValue(d)
			if err != nil {
				return nil, err
			}
			value[key] = item
		}
		_, err := d.Token()
		return value, err
	case '[':
		value := []any{}
		for d.More() {
			item, err := rpcValue(d)
			if err != nil {
				return nil, err
			}
			value = append(value, item)
		}
		_, err := d.Token()
		return value, err
	default:
		return nil, errors.New("CODEX_RPC_DELIMITER_INVALID")
	}
}

func rpcResponseID(frame map[string]any) (int, bool) {
	id, ok := frame["id"].(json.Number)
	if !ok {
		return 0, false
	}
	n, err := strconv.Atoi(string(id))
	return n, err == nil && strconv.Itoa(n) == string(id)
}
func rpcThreadEvidence(frame map[string]any, profile, cwd, source string) (string, error) {
	if id, ok := rpcResponseID(frame); !ok || id != 2 || frame["error"] != nil {
		return "", errors.New("CODEX_RPC_THREAD_RESPONSE_INVALID")
	}
	result, ok := frame["result"].(map[string]any)
	if !ok {
		return "", errors.New("CODEX_RPC_THREAD_RESULT_MISSING")
	}
	thread, ok := result["thread"].(map[string]any)
	if !ok {
		return "", errors.New("CODEX_RPC_THREAD_MISSING")
	}
	threadID, ok := thread["id"].(string)
	if !ok || threadID == "" || len(threadID) > 256 || strings.ContainsAny(threadID, "\r\n\x00") {
		return "", errors.New("CODEX_RPC_THREAD_ID_INVALID")
	}
	active, ok := result["activePermissionProfile"].(map[string]any)
	if !ok || active["id"] != profile || active["extends"] != nil {
		return "", errors.New("CODEX_RPC_ACTIVE_PROFILE_MISMATCH")
	}
	if result["cwd"] != cwd || result["approvalPolicy"] != "never" || result["approvalsReviewer"] != "user" {
		return "", errors.New("CODEX_RPC_THREAD_SETTINGS_MISMATCH")
	}
	roots, ok := result["runtimeWorkspaceRoots"].([]any)
	if !ok || len(roots) != 1 || roots[0] != source {
		return "", errors.New("CODEX_RPC_ROOTS_MISMATCH")
	}
	sandbox, ok := result["sandbox"].(map[string]any)
	if !ok || sandbox["type"] != "readOnly" || sandbox["networkAccess"] != false {
		return "", errors.New("CODEX_RPC_SANDBOX_MISMATCH")
	}
	return threadID, nil
}
func rpcFrame(raw []byte) (map[string]any, error) {
	if len(raw) == 0 || len(raw) > rpcFrameLimit || !json.Valid(raw) {
		return nil, errors.New("CODEX_RPC_FRAME_INVALID")
	}
	frame, err := rpcDecodeUnique(raw)
	if err != nil {
		return nil, err
	}
	if v, ok := frame["jsonrpc"]; ok && v != "2.0" {
		return nil, fmt.Errorf("CODEX_RPC_VERSION_INVALID: %v", v)
	}
	return frame, nil
}
