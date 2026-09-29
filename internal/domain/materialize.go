package domain

import (
	"context"
	"database/sql"
	"os"
	"path/filepath"
	"sort"
)

func (s *Service) authorizedContext(tx *sql.Tx, token, project, taskID string) (Principal, Object, error) {
	p, e := authenticate(tx, token)
	if e != nil {
		return p, nil, e
	}
	if !p.Allowed(project, taskID, "", false) && !s.runtimeScope(tx, p, project, taskID, "getTask", nil) {
		return p, nil, Fail(404, "NOT_FOUND", "task unavailable")
	}
	task, e := load(tx, project, "Task", taskID)
	if e != nil {
		return p, nil, e
	}
	if e = s.taskContext(tx, project, task); e != nil {
		return p, nil, e
	}
	bundle, e := load(tx, project, "ContextBundle", Str(task, "context_bundle_id"))
	if e != nil {
		return p, nil, e
	}
	if !s.visible(tx, p, project, bundle) {
		return p, nil, Fail(403, "FORBIDDEN", "context visibility changed")
	}
	if bundle["receipt_hash"] != Receipt(bundle) || bundle["summary_hash"] != Digest([]byte(Str(bundle, "summary"))) {
		return p, nil, Fail(422, "CONTENT_HASH_MISMATCH", "context integrity failed")
	}
	return p, bundle, nil
}

// GetTaskContext resolves the latest task pointer and rechecks the caller's current grant on every use.
func (s *Service) GetTaskContext(ctx context.Context, token, project, taskID string) (Object, error) {
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return nil, e
	}
	defer tx.Rollback()
	_, bundle, e := s.authorizedContext(tx, token, project, taskID)
	return bundle, e
}

// MaterializeTaskContext creates a new directory only. Inputs and manifests are readonly; candidates is writable.
func (s *Service) MaterializeTaskContext(ctx context.Context, token, project, taskID, destination string) (Object, error) {
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return nil, e
	}
	defer tx.Rollback()
	p, bundle, e := s.authorizedContext(tx, token, project, taskID)
	if e != nil {
		return nil, e
	}
	task, e := load(tx, project, "Task", taskID)
	if e != nil {
		return nil, e
	}
	files := map[string][]byte{}
	entries := Empty()
	seen := map[string]bool{}
	var visit func(any) error
	visit = func(v any) error {
		switch o := v.(type) {
		case map[string]any:
			if kind := Str(o, "entity_type"); kind != "" {
				key := Hash(o)
				if seen[key] {
					return nil
				}
				seen[key] = true
				obj, e := version(tx, project, o)
				if e != nil {
					return e
				}
				if !s.visible(tx, p, project, obj) {
					return Fail(403, "FORBIDDEN", "input unavailable")
				}
				if kind == "Artifact" {
					if obj["validity"] == "STALE" {
						use, proof, e := s.dependencyArtifactUse(tx, project, task, o)
						if e != nil {
							return e
						}
						var raw []byte
						if e = tx.QueryRow("SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1", project, use["storage_key"]).Scan(&raw); e != nil {
							return e
						}
						if Digest(raw) != obj["content_hash"] {
							return Fail(422, "CONTENT_HASH_MISMATCH", "re-proven result bytes changed")
						}
						name := Str(obj, "id") + ".content"
						files[name] = raw
						entries = append(entries, Object{"path": "inputs/" + name, "ref": o, "content_hash": obj["content_hash"], "access_class": obj["access_class"], "use_receipt_hash": use["receipt_hash"], "proof_ref": proof, "canonical_validity": "STALE"})
						if e = visit(proof); e != nil {
							return e
						}
						return nil // Historical primary inputs are not this contribution inputs.
					}

					if obj["access_class"] != "PROJECT" {
						return Fail(503, "RESOURCE_UNAVAILABLE", "protected content requires W17")
					}
					var raw []byte
					if e = tx.QueryRow("SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1", project, obj["storage_key"]).Scan(&raw); e != nil {
						return e
					}
					if Digest(raw) != obj["content_hash"] {
						return Fail(422, "CONTENT_HASH_MISMATCH", "input bytes changed")
					}
					name := Str(obj, "id") + ".content"
					files[name] = raw
					entries = append(entries, Object{"path": "inputs/" + name, "ref": o, "content_hash": obj["content_hash"], "access_class": obj["access_class"]})
				}
				if e = visit(obj); e != nil {
					return e
				}
			}
			for _, v := range o {
				if e = visit(v); e != nil {
					return e
				}
			}
		case []any:
			for _, v := range o {
				if e = visit(v); e != nil {
					return e
				}
			}
		}
		return nil
	}
	if e = visit(bundle); e != nil {
		return nil, e
	}
	if e = tx.Commit(); e != nil {
		return nil, e
	}
	destination, e = filepath.Abs(destination)
	if e != nil {
		return nil, e
	}
	if _, e = os.Stat(destination); !os.IsNotExist(e) {
		return nil, Fail(409, "STATE_CONFLICT", "destination must not exist")
	}
	if e = os.MkdirAll(filepath.Dir(destination), 0700); e != nil {
		return nil, e
	}
	stage, e := os.MkdirTemp(filepath.Dir(destination), ".researchos-context-")
	if e != nil {
		return nil, e
	}
	created := []string{}
	success := false
	defer func() {
		if !success {
			for _, p := range created {
				os.Chmod(p, 0600)
				os.Remove(p)
			}
			os.Remove(filepath.Join(stage, "inputs"))
			os.Remove(filepath.Join(stage, "candidates"))
			os.Remove(stage)
		}
	}()
	if e = os.Mkdir(filepath.Join(stage, "inputs"), 0700); e != nil {
		return nil, e
	}
	if e = os.Mkdir(filepath.Join(stage, "candidates"), 0700); e != nil {
		return nil, e
	}
	sort.Slice(entries, func(i, j int) bool {
		return Str(entries[i].(map[string]any), "path") < Str(entries[j].(map[string]any), "path")
	})
	manifest := Object{"project_id": project, "task_id": taskID, "bundle_ref": Ref(bundle, "ContextBundle"), "version_vector": bundle["version_vector"], "input_manifest": entries, "source_manifest_hash": bundle["source_manifest_hash"], "candidate_directory": "candidates", "resume_instruction": "Read the frozen bundle and produce candidates; acceptance requires the independent service."}
	files["../bundle.json"] = Bytes(bundle)
	files["../manifest.json"] = Bytes(manifest)
	for name, raw := range files {
		path := filepath.Join(stage, "inputs", name)
		if e = os.WriteFile(path, raw, 0600); e != nil {
			return nil, e
		}
		created = append(created, path)
		if e = os.Chmod(path, 0444); e != nil {
			return nil, e
		}
	}
	if e = os.Rename(stage, destination); e != nil {
		return nil, e
	}
	success = true
	return manifest, nil
}
