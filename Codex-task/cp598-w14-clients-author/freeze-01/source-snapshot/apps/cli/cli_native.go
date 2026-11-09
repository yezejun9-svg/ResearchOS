package main

import (
	"bytes"
	"crypto/rand"
	"crypto/sha256"
	"encoding/json"
	"encoding/json/jsontext"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"time"
	"unicode/utf8"

	"researchos.local/research-os/internal/host"
)

// Private pilot constants intentionally do not depend on an unadopted Host API.
const cliNativeAttestRequest = "NATIVE_CLIENT_ATTEST_REQUEST"
const cliNativeAttestResult = "NATIVE_CLIENT_ATTEST_RESULT"
const cliNativeAttestHeader = "X-ResearchOS-Native-Attestation"

var cliAttestationRefPattern = regexp.MustCompile(`^natt-[0-9a-f]{64}$`)
var cliClientInstancePattern = regexp.MustCompile(`^nci-[0-9a-f]{32}$`)

func cliClosedNativeJSON(raw []byte, target any) error {
	if len(raw) == 0 || len(raw) > 8192 || !jsontext.Value(raw).IsValid() {
		return errors.New("NATIVE_ATTESTATION_INVALID")
	}
	decoder := json.NewDecoder(bytes.NewReader(raw))
	decoder.DisallowUnknownFields()
	if decoder.Decode(target) != nil || decoder.Decode(new(any)) != io.EOF {
		return errors.New("NATIVE_ATTESTATION_INVALID")
	}
	return nil
}

// The commitment describes final HTTP bytes and the bearer chosen for this
// attempt. Only the Host's current private witness map can turn it into proof.
func cliAttestCreate(c *v2Context, env *v2Envelope, raw []byte) (string, error) {
	refuse := errors.New("NATIVE_CREATE_ATTESTATION_UNAVAILABLE")
	if env.Method != "session.create" || env.ProjectID == nil || *env.ProjectID == "" ||
		env.SessionID != nil || env.ExpectedRevision != nil || env.WriterEpoch != nil ||
		!commandIDPattern.MatchString(env.CommandID) || c.credential == "" || !utf8.ValidString(c.credential) || utf8.RuneCountInString(c.credential) > 1024 {
		return "", refuse
	}
	resolved, err := resolveCLIHostDiscovery()
	if err != nil || resolved.discovery.URL != c.baseURL {
		return "", refuse
	}
	d := resolved.discovery
	id, err := cliHostInstanceID(d)
	if err != nil {
		return "", refuse
	}
	digest := sha256.Sum256(raw)
	frame, err := json.Marshal(map[string]any{"kind": cliNativeAttestRequest, "client_id": env.ClientID,
		"payload": map[string]any{"schema_version": 1, "credential_value": c.credential,
			"command_id": env.CommandID, "method": "session.create", "project_id": *env.ProjectID,
			"request_raw_sha256": fmt.Sprintf("sha256:%x", digest), "session_id": nil,
			"expected_revision": nil, "writer_epoch": nil}})
	if err != nil || len(frame) > 8192 {
		return "", refuse
	}
	replyRaw, err := cliNativeDial(host.PipeName(id), frame)
	if err != nil {
		return "", refuse // Never expose native error args, bearer or witness ref.
	}
	var reply struct {
		Kind    string          `json:"kind"`
		Payload json.RawMessage `json:"payload"`
	}
	if cliClosedNativeJSON(replyRaw, &reply) != nil || reply.Kind != cliNativeAttestResult {
		return "", refuse
	}
	var proof struct {
		Schema         int    `json:"schema_version"`
		Ref            string `json:"attestation_ref"`
		ClientInstance string `json:"client_instance_ref"`
		HostID         string `json:"host_instance_id"`
		ExpiresAt      string `json:"expires_at"`
	}
	if cliClosedNativeJSON(reply.Payload, &proof) != nil || proof.Schema != 1 ||
		!cliAttestationRefPattern.MatchString(proof.Ref) || !cliClientInstancePattern.MatchString(proof.ClientInstance) || proof.HostID != id {
		return "", refuse
	}
	expires, err := time.Parse(time.RFC3339Nano, proof.ExpiresAt)
	if err != nil || !time.Now().Before(expires) {
		return "", refuse
	}
	currentID, err := cliHostInstanceID(d)
	if err != nil || currentID != id {
		return "", refuse
	}
	return proof.Ref, nil
}

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
	resolved, err := resolveCLIHostDiscovery()
	if err != nil {
		return "", err
	}
	actual := resolved.discovery
	if d.URL == "" || d.DataDir == "" || actual.URL != d.URL || actual.PID != d.PID || actual.DataDir != d.DataDir {
		return "", errors.New("HOST_NATIVE_DISCOVERY_INCOMPLETE")
	}
	id := resolved.hostID
	if id == "" {
		// Preserve the older explicit/cwd launcher's native identity fallback.
		// Shared locators require a direct, matching ID in the resolver already.
		current, err := readCLIHost(filepath.Join(d.DataDir, "discovery.json"), nil)
		if err != nil || current.discovery.URL != d.URL || current.discovery.PID != d.PID || current.discovery.DataDir != d.DataDir {
			return "", errors.New("HOST_NATIVE_DISCOVERY_MISMATCH")
		}
		id = current.hostID
	}
	if !cliHostIDPattern.MatchString(id) {
		return "", errors.New("HOST_NATIVE_DISCOVERY_INCOMPLETE")
	}
	return id, nil
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
