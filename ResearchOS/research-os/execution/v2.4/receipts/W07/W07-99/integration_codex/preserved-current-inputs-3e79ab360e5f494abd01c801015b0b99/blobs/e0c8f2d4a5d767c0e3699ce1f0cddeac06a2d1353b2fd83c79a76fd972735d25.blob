//go:build windows

package domain

import (
	"bytes"
	"context"
	"database/sql"
	"debug/buildinfo"
	"fmt"

	"researchos.local/research-os/evaluation/evolution"
)

type controlHostRegistration struct {
	SnapshotRef      Object
	StableSourceHash string
	Current          Object
}

// RegisterEvolutionControlFixture is a fresh host registration, never an update
// of a calculator host or a recompilation under an old stable identity. It is
// local provisioning, not a route, queue, OS qualification or cutover command.
func (s *Service) RegisterEvolutionControlFixture(ctx context.Context, project, supervisorID, releasePrincipal, root string, stable, suite, rollback, snapshotRef Object, stableSourceHash string) error {
	if err := s.Contracts.Validate("Digest", stableSourceHash); err != nil {
		return err
	}
	return s.registerEvolutionFixtureProfile(ctx, project, supervisorID, releasePrincipal, root, stable, suite, rollback, false, &controlHostRegistration{SnapshotRef: snapshotRef, StableSourceHash: stableSourceHash})
}

func controlHost(h Object) bool { return h["evaluation_profile"] == evolution.ControlProfile }

func validateControlBuild(raw []byte) error {
	info, err := buildinfo.Read(bytes.NewReader(raw))
	if err != nil || info.Path != "researchos.local/research-os/apps/control" || info.Main.Path != "researchos.local/research-os" {
		return fmt.Errorf("CONTROL_EXACT_APPLICATION_BUILD_REQUIRED")
	}
	settings := map[string]string{}
	for _, setting := range info.Settings {
		settings[setting.Key] = setting.Value
	}
	if settings["GOOS"] != "windows" || settings["GOARCH"] != "amd64" {
		return fmt.Errorf("CONTROL_WINDOWS_BUILD_REQUIRED")
	}
	return nil
}

// Candidate code may change these business implementations only. All replay,
// scoring, labels, acceptance, sandbox, supervisor, release and schema code is
// outside the permitted manifest and remains part of the reviewed baseline.
func controlBuildManifest(m Object) bool {
	allowed := map[string]bool{"internal/domain/research.go": true, "internal/domain/research_close.go": true, "internal/domain/research_acceptance.go": true}
	paths := Arr(m, "paths")
	if len(m) != 1 || len(paths) == 0 || len(paths) > len(allowed) {
		return false
	}
	seen := map[string]bool{}
	for _, v := range paths {
		p, ok := v.(string)
		if !ok || !allowed[p] || seen[p] {
			return false
		}
		seen[p] = true
	}
	return true
}

func (s *Service) controlHostInputs(tx *sql.Tx, project string, h Object) (evolution.ControlBundle, evolution.ControlSuite, error) {
	var bundle evolution.ControlBundle
	var suite evolution.ControlSuite
	if !controlHost(h) || h["os_service_qualified"] != false || h["protocol"] != evolution.ControlProtocol {
		return bundle, suite, Fail(422, "GATE_FAILED", "control profile host required")
	}
	ref, ok := h["snapshot_ref"].(map[string]any)
	if !ok {
		return bundle, suite, fmt.Errorf("CONTROL_SNAPSHOT_REFERENCE")
	}
	_, raw, err := s.evolutionBytes(tx, project, ref)
	if err != nil {
		return bundle, suite, err
	}
	if err = evolution.StrictControlJSON(raw, &bundle); err != nil {
		return bundle, suite, err
	}
	if err = bundle.Validate(); err != nil {
		return bundle, suite, err
	}
	if Hash(bundle.Binding) != Hash(h["control_binding"]) {
		return bundle, suite, fmt.Errorf("CONTROL_HOST_SNAPSHOT_BINDING")
	}
	_, raw, err = s.evolutionBytes(tx, project, h["suite_ref"].(map[string]any))
	if err != nil {
		return bundle, suite, err
	}
	if err = evolution.StrictControlJSON(raw, &suite); err != nil {
		return bundle, suite, err
	}
	if err = evolution.ValidateControlDataset(suite.Inputs, suite.Labels); err != nil {
		return bundle, suite, err
	}
	if suite.Inputs.Revision != evolution.ControlPublicRevision || suite.Inputs.Binding != bundle.Binding || Digest(raw) != h["public_suite_hash"] || Digest(evolution.Bytes(suite)) != Digest(raw) || h["policy_hash"] != Digest(evolution.Bytes(evolution.ControlPolicy(bundle.Binding, Digest(raw)))) {
		return bundle, suite, fmt.Errorf("CONTROL_HOST_POLICY_BINDING")
	}
	return bundle, suite, nil
}

func (s *Service) controlBuildSources(tx *sql.Tx, project string, x, h Object) (string, string, error) {
	var raw string
	if err := tx.QueryRow("SELECT body FROM evolution_builds WHERE project=? AND artifact=?", project, x["candidate_artifact_ref"].(map[string]any)["id"]).Scan(&raw); err != nil {
		return "", "", err
	}
	build, err := Decode([]byte(raw))
	if err != nil {
		return "", "", err
	}
	if build["evaluation_profile"] != evolution.ControlProfile || build["protocol"] != evolution.ControlProtocol || Hash(build["control_binding"]) != Hash(h["control_binding"]) {
		return "", "", fmt.Errorf("CONTROL_BUILD_PROFILE_BINDING")
	}
	return Str(h, "stable_source_hash"), Str(build, "source_hash"), nil
}

func evolutionSuiteHash(h Object) string {
	if controlHost(h) {
		return Str(h, "public_suite_hash")
	}
	return Digest(evolution.Bytes(evolution.Suite()))
}

func evolutionPolicyHash(h Object) string {
	if controlHost(h) {
		return Str(h, "policy_hash")
	}
	return Digest(evolution.Bytes(evolution.Policy()))
}

func (s *Service) evolutionHostCaseIDs(tx *sql.Tx, project string, h Object) ([]any, error) {
	if !controlHost(h) {
		return evolutionIDs(), nil
	}
	_, suite, err := s.controlHostInputs(tx, project, h)
	if err != nil {
		return nil, err
	}
	ids := Empty()
	for _, c := range suite.Inputs.Cases {
		ids = append(ids, c.ID)
	}
	return ids, nil
}

func evolutionHostExpected(h Object, phase string) Object {
	if !controlHost(h) {
		return evolutionExpected(phase)
	}
	return Object{"suite_hash": evolutionSuiteHash(h), "phase": phase, "scope": evolution.Scope, "profile": evolution.ControlProfile, "protocol": evolution.ControlProtocol, "control_binding": h["control_binding"]}
}
