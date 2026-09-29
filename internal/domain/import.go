package domain

import (
	"context"
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

type importFile struct {
	path string
	raw  []byte
}

// ImportSpecification accepts only a caller-pinned package. Neither documents nor manifests grant authority.
// The credential is read from a private file by the CLI, never from command arguments.
func (s *Service) ImportSpecification(ctx context.Context, token, root, expected string, options Object) (Object, error) {
	for k := range options {
		if k != "assumptions" {
			return nil, Fail(400, "INVALID_REQUEST", "import option cannot grant historical authority")
		}
	}
	assumptions := Empty()
	if v, ok := options["assumptions"]; ok {
		a, ok := v.([]any)
		if !ok {
			return nil, Fail(400, "INVALID_REQUEST", "assumptions array required")
		}
		for _, v := range a {
			text, ok := v.(string)
			if !ok || strings.TrimSpace(text) == "" {
				return nil, Fail(400, "INVALID_REQUEST", "explicit assumption text required")
			}
			assumptions = append(assumptions, text)
		}
	}
	absolute, e := filepath.Abs(root)
	if e != nil {
		return nil, e
	}
	absolute, e = filepath.EvalSymlinks(absolute)
	if e != nil {
		return nil, e
	}
	raw, e := os.ReadFile(filepath.Join(absolute, "PACKAGE_MANIFEST.json"))
	if e != nil {
		return nil, e
	}
	if Digest(raw) != expected {
		return nil, Fail(422, "CONTENT_HASH_MISMATCH", "pinned manifest differs")
	}
	manifest, e := Decode(raw)
	if e != nil {
		return nil, e
	}
	allowed := " package_id package_version specification_date user_timezone status product_implementation_status product_test_status entrypoint execution_goal source_snapshot requirement_ids task_ids case_ids generated_report integrity_note files ui_screen_ids document_count additional_sources "
	for k := range manifest {
		if !strings.Contains(allowed, " "+k+" ") {
			return nil, Fail(400, "INVALID_REQUEST", "manifest field is not a package field")
		}
	}
	if manifest["package_id"] != "researchos-implementation-spec" || manifest["product_test_status"] != "NOT_RUN" {
		return nil, Fail(422, "GATE_FAILED", "ResearchOS specification package required")
	}
	files := []importFile{{"PACKAGE_MANIFEST.json", raw}}
	seen := map[string]bool{}
	for _, v := range Arr(manifest, "files") {
		entry, ok := v.(map[string]any)
		if !ok {
			return nil, Fail(400, "INVALID_REQUEST", "invalid manifest entry")
		}
		name := Str(entry, "path")
		if name == "" || strings.Contains(name, "\\") || strings.Contains(name, ":") || strings.HasPrefix(name, "/") || filepath.ToSlash(filepath.Clean(name)) != name || strings.HasPrefix(name, "../") || name == ".." || seen[name] {
			return nil, Fail(400, "INVALID_REQUEST", "invalid package path")
		}
		seen[name] = true
		path := filepath.Join(absolute, filepath.FromSlash(name))
		resolved, e := filepath.EvalSymlinks(path)
		if e != nil {
			return nil, e
		}
		rel, e := filepath.Rel(absolute, resolved)
		if e != nil || strings.HasPrefix(rel, "..") || filepath.IsAbs(rel) {
			return nil, Fail(403, "FORBIDDEN", "package path escapes source")
		}
		info, e := os.Stat(path)
		if e != nil || !info.Mode().IsRegular() || info.Size() > 64*1024*1024 {
			return nil, Fail(400, "INVALID_REQUEST", "invalid source file")
		}
		data, e := os.ReadFile(path)
		if e != nil {
			return nil, e
		}
		size, e := Num(entry, "size_bytes")
		if e != nil {
			return nil, e
		}
		if int64(len(data)) != size || Digest(data) != "sha256:"+Str(entry, "sha256") {
			return nil, Fail(422, "CONTENT_HASH_MISMATCH", "package file differs: "+name)
		}
		files = append(files, importFile{name, data})
	}
	if len(seen) == 0 {
		return nil, Fail(422, "GATE_FAILED", "empty package")
	}
	e = filepath.WalkDir(absolute, func(path string, d fs.DirEntry, walkErr error) error {
		if walkErr != nil {
			return walkErr
		}
		if d.Type()&os.ModeSymlink != 0 {
			return Fail(403, "FORBIDDEN", "package links are forbidden")
		}
		if d.IsDir() {
			if d.Name() == "__pycache__" {
				return filepath.SkipDir
			}
			return nil
		}
		rel, _ := filepath.Rel(absolute, path)
		name := filepath.ToSlash(rel)
		if !seen[name] && name != "PACKAGE_MANIFEST.json" && name != "PACKAGE_VALIDATION.json" {
			return Fail(422, "GATE_FAILED", "unlisted package file")
		}
		return nil
	})
	if e != nil {
		return nil, e
	}
	sort.Slice(files, func(i, j int) bool { return files[i].path < files[j].path })
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return nil, e
	}
	defer tx.Rollback()
	p, e := authenticate(tx, token)
	if e != nil {
		return nil, e
	}
	if !p.HasRole("OWNER") || !p.CanCreateProject {
		return nil, Fail(403, "FORBIDDEN", "explicit Owner project creation required")
	}
	profile, e := s.createProject(tx, p, Object{"name": "ResearchOS", "intent": "Implement the pinned ResearchOS specification as its own initial managed project.", "facts": Empty(), "accepted_scope": []any{"ResearchOS specification package"}, "constraints": Empty(), "source_configs": Empty(), "source_document_refs": Empty(), "read_snapshot_ids": Empty()})
	if e != nil {
		return nil, e
	}
	project := Str(profile, "project_id")
	refs := Empty()
	byPath := map[string]Object{}
	inventory := Empty()
	var manifestArtifact Object
	for _, file := range files {
		kind := "SOURCE_SNAPSHOT"
		if file.path == "PACKAGE_MANIFEST.json" {
			kind = "MANIFEST"
		}
		a, e := s.serverArtifact(tx, project, p.ID, kind, file.raw, Empty())
		if e != nil {
			return nil, e
		}
		byPath[file.path] = a
		refs = append(refs, Ref(a, "Artifact"))
		inventory = append(inventory, Object{"path": file.path, "artifact_ref": Ref(a, "Artifact"), "sha256": a["content_hash"]})
		if kind == "MANIFEST" {
			manifestArtifact = a
		}
	}
	goalSource, ok := byPath[Str(manifest, "execution_goal")]
	if !ok {
		return nil, Fail(422, "GATE_FAILED", "execution goal source missing")
	}
	facts := []any{Object{"text": "The pinned package requests implementation of ResearchOS.", "basis": "USER_STATED", "source_refs": []any{Ref(goalSource, "Artifact")}, "validity": "CURRENT"}, Object{"text": fmt.Sprintf("Verified %d package files against the pinned manifest.", len(seen)), "basis": "OBSERVED", "source_refs": []any{Ref(manifestArtifact, "Artifact")}, "validity": "CURRENT"}, Object{"text": "The package technical design is a proposed implementation baseline.", "basis": "PROPOSED", "source_refs": []any{Ref(byPath["02_TECHNICAL_DESIGN.md"], "Artifact")}, "validity": "CURRENT"}}
	for _, text := range assumptions {
		facts = append(facts, Object{"text": text, "basis": "ASSUMED", "source_refs": Empty(), "validity": "CURRENT"})
	}
	profile["facts"] = facts
	profile["source_document_refs"] = refs
	if e = bump(profile); e != nil {
		return nil, e
	}
	if e = s.put(tx, "ProjectProfile", profile); e != nil {
		return nil, e
	}
	req, e := s.createRequirement(tx, project, Object{"requirement_key": "RESEARCHOS-INITIAL-GOAL", "text": "Implement the frozen ResearchOS execution goal with all mandatory acceptance cases.", "basis": "USER_STATED", "source_refs": []any{Ref(goalSource, "Artifact")}, "rationale": "Explicit pinned specification import", "supersedes_id": nil, "acceptance_check_ids": manifest["case_ids"]})
	if e != nil {
		return nil, e
	}
	req, e = s.actRequirement(tx, project, Str(req, "id"), Object{"action": "ACCEPT", "reason": "Owner explicitly imported the specification as the initial goal", "source_validation_refs": []any{Ref(manifestArtifact, "Artifact")}})
	if e != nil {
		return nil, e
	}
	var acceptance Object
	for _, file := range files {
		if file.path == "contracts/acceptance.json" {
			acceptance, e = Decode(file.raw)
			if e != nil {
				return nil, e
			}
		}
	}
	if acceptance == nil {
		return nil, Fail(422, "GATE_FAILED", "acceptance source missing")
	}
	checks := Empty()
	for _, v := range Arr(acceptance, "cases") {
		c := v.(map[string]any)
		commands := Arr(c, "command_keys")
		if len(commands) == 0 {
			return nil, Fail(422, "GATE_FAILED", "case command missing")
		}
		command := commands[len(commands)-1]
		expected := []string{}
		for _, v := range Arr(c, "expected") {
			expected = append(expected, v.(string))
		}
		checks = append(checks, Object{"check_id": c["id"], "kind": "DETERMINISTIC", "required": true, "expected": strings.Join(expected, "\n"), "command_key": command, "rubric_ref": nil, "qualification_id": nil, "not_applicable_reason": nil})
	}
	if len(checks) != len(Arr(manifest, "case_ids")) {
		return nil, Fail(422, "GATE_FAILED", "acceptance inventory mismatch")
	}
	contract := Object{"contract_hash": Hash(checks), "contract_revision": 1, "checks": checks, "require_independent_verifier": true, "version_policy": "EXACT", "frozen_at": Now()}
	goal, e := s.createGoal(tx, project, Object{"title": "Implement ResearchOS", "original_intent": "Implement the pinned ResearchOS execution goal", "scope": "PROJECT", "requirement_refs": []any{Ref(req, "Requirement")}, "problem_ids": []any{"researchos-initial-intent"}, "deliverables": []any{"ResearchOS implementation and all required evidence"}, "acceptance_contract": contract})
	if e != nil {
		return nil, e
	}
	state, e := singleton(tx, project, "ProjectState")
	if e != nil {
		return nil, e
	}
	state["profile_revision"] = profile["revision"]
	if e = bump(state); e != nil {
		return nil, e
	}
	if e = s.put(tx, "ProjectState", state); e != nil {
		return nil, e
	}
	if _, e = tx.Exec("INSERT INTO context_imports(project,manifest_hash,manifest_artifact_id,inventory) VALUES(?,?,?,?)", project, expected, manifestArtifact["id"], string(Bytes(inventory))); e != nil {
		return nil, e
	}
	if e = s.event(tx, project, "Goal", goal, p.ID, ID(), "PROJECT_UPDATED"); e != nil {
		return nil, e
	}
	if e = tx.Commit(); e != nil {
		return nil, e
	}
	return Object{"project_id": project, "profile": profile, "goal": goal, "manifest_hash": expected, "inventory": inventory, "product_tests": "NOT_RUN", "scope": "SPECIFICATION_IMPORT_ONLY"}, nil
}
