package main

import (
	"crypto/rand"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"time"

	"researchos.local/research-os/internal/host"
)

// The native bridge is the only path from a CLI path hint to a trusted selection.
// The host's folder picker still requires the user's confirmation.
var cliNativeDial = host.DialNative

var cliHostIDPattern = regexp.MustCompile(`^host-[0-9a-f]{12}$`)

type cliNativeReply struct {
	Kind    string          `json:"kind"`
	Payload json.RawMessage `json:"payload"`
	Error   struct {
		Code string `json:"code"`
	} `json:"error"`
}

func cliHostInstanceID(d discovery) (string, error) {
	// Discovery is written by the local control process. Keep this field local to
	// first-use until every older CLI call site has migrated to the new discovery.
	raw, err := os.ReadFile(productDiscoveryFile())
	if err != nil {
		return "", err
	}
	var id struct {
		URL            string `json:"url"`
		PID            int    `json:"pid"`
		DataDir        string `json:"data_dir"`
		HostInstanceID string `json:"host_instance_id"`
	}
	if err := json.Unmarshal(raw, &id); err != nil {
		return "", err
	}
	if d.URL == "" || d.DataDir == "" || id.URL != d.URL || id.PID != d.PID || id.DataDir != d.DataDir {
		return "", errors.New("HOST_NATIVE_DISCOVERY_INCOMPLETE")
	}
	if id.HostInstanceID == "" {
		// An older launcher discovery lacks the native id. The control process
		// writes its own current file; accept that identity only when the three
		// launcher identity fields match exactly.
		fallback, err := os.ReadFile(filepath.Join(d.DataDir, "discovery.json"))
		if err != nil {
			return "", errors.New("HOST_NATIVE_DISCOVERY_INCOMPLETE")
		}
		var current struct {
			URL            string `json:"url"`
			PID            int    `json:"pid"`
			DataDir        string `json:"data_dir"`
			HostInstanceID string `json:"host_instance_id"`
		}
		if err := json.Unmarshal(fallback, &current); err != nil || current.URL != d.URL || current.PID != d.PID || current.DataDir != d.DataDir {
			return "", errors.New("HOST_NATIVE_DISCOVERY_MISMATCH")
		}
		id.HostInstanceID = current.HostInstanceID
	}
	if !cliHostIDPattern.MatchString(id.HostInstanceID) {
		return "", errors.New("HOST_NATIVE_DISCOVERY_INCOMPLETE")
	}
	return id.HostInstanceID, nil
}

func cliFirstUseCommandID(step string) (string, error) {
	var entropy [12]byte
	if _, err := rand.Read(entropy[:]); err != nil {
		return "", err
	}
	return fmt.Sprintf("cmd-init-%s-%x", step, entropy), nil
}

func cliNativeRequest(d discovery, clientID, kind string, payload map[string]any) (json.RawMessage, error) {
	id, err := cliHostInstanceID(d)
	if err != nil {
		return nil, err
	}
	frame, err := json.Marshal(map[string]any{"kind": kind, "client_id": clientID, "payload": payload})
	if err != nil {
		return nil, err
	}
	raw, err := cliNativeDial(host.PipeName(id), frame)
	if err != nil {
		return nil, err
	}
	var reply cliNativeReply
	if err := json.Unmarshal(raw, &reply); err != nil {
		return nil, errors.New("NATIVE_MALFORMED_REPLY")
	}
	if reply.Kind == "NATIVE_ERROR" {
		return nil, fmt.Errorf("NATIVE_%s", orDefault(reply.Error.Code, "ERROR"))
	}
	want := strings.TrimSuffix(kind, "_REQUEST") + "_RESULT"
	if reply.Kind != want || len(reply.Payload) == 0 {
		return nil, errors.New("NATIVE_WRONG_REPLY")
	}
	return reply.Payload, nil
}

// Read the current local credential. Renewal uses the authenticated native pipe;
// neither this file nor a renewal asks the user to copy a short-lived token.
func cliSessionCredential(d discovery) (string, error) {
	if d.DataDir == "" {
		return "", errors.New("HOST_DATA_DIR_ABSENT")
	}
	path := filepath.Join(d.DataDir, "host", "session.json")
	info, err := os.Lstat(path)
	if err != nil {
		return "", err
	}
	if !info.Mode().IsRegular() || info.Size() <= 0 || info.Size() > 8192 {
		return "", errors.New("HOST_SESSION_FILE_INVALID")
	}
	raw, err := os.ReadFile(path)
	if err != nil {
		return "", err
	}
	var session struct {
		Token     string `json:"token"`
		ExpiresAt string `json:"expires_at"`
	}
	if err := json.Unmarshal(raw, &session); err != nil {
		return "", errors.New("HOST_SESSION_FILE_INVALID")
	}
	exp, err := time.Parse(time.RFC3339Nano, session.ExpiresAt)
	if err != nil || session.Token == "" || !time.Now().Before(exp) {
		return "", errors.New("HOST_SESSION_EXPIRED")
	}
	return session.Token, nil
}

func cliInitCredential(d discovery, clientID string) (string, error) {
	if explicit := os.Getenv("RESEARCHOS_CLI_CREDENTIAL"); explicit != "" {
		return explicit, nil
	}
	if token, err := cliSessionCredential(d); err == nil {
		return token, nil
	}
	if _, err := cliNativeRequest(d, clientID, host.KindUserBootstrapRequest, map[string]any{}); err != nil {
		return "", err
	}
	return cliSessionCredential(d)
}

func cliChooseWorkspace(d discovery, clientID, path string) (string, string, error) {
	payload, err := cliNativeRequest(d, clientID, host.KindWorkspaceChooseRequest,
		map[string]any{"requested_path": path, "requested_access": "READ_WRITE"})
	if err != nil {
		return "", "", err
	}
	var choice struct {
		SelectionRef string `json:"selection_ref"`
		DisplayPath  string `json:"display_path"`
	}
	if err := json.Unmarshal(payload, &choice); err != nil || choice.SelectionRef == "" || choice.DisplayPath == "" {
		return "", "", errors.New("NATIVE_CHOICE_INVALID")
	}
	return choice.SelectionRef, choice.DisplayPath, nil
}
