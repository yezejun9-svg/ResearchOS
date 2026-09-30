package domain

import (
	"context"
	"database/sql"
	"encoding/base64"
	"encoding/hex"
	"errors"
	"net/http"
	"researchos.local/research-os/adapters/protectedstore"
	"strings"
)

func protectedAllowed(p Principal, project string) bool {
	return (p.HasRole("OWNER") || p.HasRole("VERIFIER")) && p.Allowed(project, "", "", true)
}
func protectedFailure(e error) error {
	if errors.Is(e, protectedstore.ErrIntegrity) {
		return Fail(422, "CONTENT_HASH_MISMATCH", "protected bytes failed integrity verification")
	}
	if errors.Is(e, protectedstore.ErrNotFound) {
		return Fail(404, "NOT_FOUND", "protected body unavailable")
	}
	return Fail(503, "RESOURCE_UNAVAILABLE", "protected provider or independent identity boundary is unavailable")
}
func (s *Service) protectedReady(ctx context.Context, mode string) error {
	if s.Protected == nil {
		return protectedFailure(protectedstore.ErrUnavailable)
	}
	if e := s.Protected.Ready(ctx, mode); e != nil {
		return protectedFailure(e)
	}
	boundary, e := s.Protected.Boundary(ctx)
	if e != nil {
		return protectedFailure(e)
	}
	if mode == "LIVE" && (!boundary.IndependentIdentity || boundary.UnrestrictedSameUserCanRead || boundary.Mode != "INDEPENDENT_VERIFIER") {
		return protectedFailure(protectedstore.ErrIsolation)
	}
	if mode != "LIVE" && mode != "FIXTURE" {
		return Fail(422, "GATE_FAILED", "protected measurement mode required")
	}
	return nil
}

// RegisterProtectedArtifact receives only an opaque ticket from a trusted
// provider. Private bytes never pass through ordinary upload/seal or enter the
// uploaded_content table. Only current restricted Owner/Verifier grants may
// register metadata; registration is not qualification or declassification.
func (s *Service) RegisterProtectedArtifact(ctx context.Context, token, project, ticket string, b Object) (Object, error) {
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return nil, e
	}
	p, e := authenticate(tx, token)
	if e == nil && !protectedAllowed(p, project) {
		e = Fail(403, "FORBIDDEN", "restricted verifier or owner grant required")
	}
	if e == nil && !s.visible(tx, p, project, b) {
		e = Fail(403, "FORBIDDEN", "protected input lineage is not authorized")
	}
	if e == nil {
		for _, ref := range semanticReferences("Artifact", b) {
			if e = s.effective(tx, project, ref); e != nil {
				break
			}
		}
	}
	tx.Rollback()
	if e != nil {
		return nil, e
	}
	if e = s.protectedReady(ctx, Str(b, "measurement_mode")); e != nil {
		return nil, e
	}
	descriptor, e := s.Protected.Describe(ctx, project, ticket)
	if e != nil {
		return nil, protectedFailure(e)
	}
	if !descriptor.Valid() || descriptor.Project != project || descriptor.Ticket != ticket || descriptor.MeasurementMode != b["measurement_mode"] {
		return nil, Fail(422, "GATE_FAILED", "protected descriptor binding mismatch")
	}
	raw, e := s.Protected.Read(ctx, descriptor)
	if e != nil {
		return nil, protectedFailure(e)
	}
	if Digest(raw) != descriptor.Hash || int64(len(raw)) != descriptor.Size {
		return nil, protectedFailure(protectedstore.ErrIntegrity)
	}
	// No raw bytes are persisted by the control plane, including on error.
	raw = nil
	if e = s.protectedReady(ctx, descriptor.MeasurementMode); e != nil {
		return nil, e
	}
	tx, e = s.DB.BeginTx(ctx, nil)
	if e != nil {
		return nil, e
	}
	defer tx.Rollback()
	current, e := authenticate(tx, token)
	if e != nil {
		return nil, e
	}
	if current.ID != p.ID || !protectedAllowed(current, project) || !s.visible(tx, current, project, b) {
		return nil, Fail(403, "FORBIDDEN", "protected registration authority changed")
	}
	for _, ref := range semanticReferences("Artifact", b) {
		if e = s.effective(tx, project, ref); e != nil {
			return nil, e
		}
	}
	b = copyObject(b)
	b["storage_key"] = descriptor.Ticket
	b["content_hash"] = descriptor.Hash
	b["byte_size"] = descriptor.Size
	b["media_type"] = descriptor.MediaType
	b["access_class"] = "VERIFIER_ONLY"
	b["produced_by"] = p.ID
	if b["run_id"] != nil {
		return nil, Fail(422, "GATE_FAILED", "protected registration is a trusted host operation, not an executor contribution")
	}
	if e = s.Contracts.Validate("CreateArtifactRequest", b); e != nil {
		return nil, Fail(400, "INVALID_REQUEST", "protected artifact metadata violates schema")
	}
	var priorRaw string
	e = tx.QueryRow("SELECT body FROM domain_objects WHERE project=? AND kind='Artifact' AND json_extract(body,'$.content_hash')=? AND json_extract(body,'$.kind')=?", project, descriptor.Hash, b["kind"]).Scan(&priorRaw)
	if e == nil {
		prior, err := Decode([]byte(priorRaw))
		if err != nil {
			return nil, err
		}
		if prior["access_class"] != "VERIFIER_ONLY" || prior["storage_key"] != descriptor.Ticket {
			return nil, Fail(409, "STATE_CONFLICT", "protected and public content cannot be silently reclassified or rebound")
		}
		if err = s.reusableArtifact(tx, p, project, prior, b, nil); err != nil {
			return nil, err
		}
		return prior, tx.Commit()
	}
	if e != sql.ErrNoRows {
		return nil, e
	}
	artifact := Merge(Base(project), b)
	artifact["validity"] = "CURRENT"
	artifact["sealed_at"] = Now()
	if e = s.put(tx, "Artifact", artifact); e != nil {
		return nil, e
	}
	for _, field := range []string{"input_refs", "source_refs"} {
		for _, ref := range Arr(b, field) {
			if _, e = s.impactLink(tx, project, Object{"from_ref": Ref(artifact, "Artifact"), "to_ref": ref, "relation": "DERIVED_FROM", "basis": "DETERMINISTIC", "evidence_refs": Empty()}); e != nil {
				return nil, e
			}
		}
	}
	if e = s.event(tx, project, "Artifact", artifact, p.ID, ID(), "PROJECT_UPDATED"); e != nil {
		return nil, e
	}
	if e = tx.Commit(); e != nil {
		return nil, e
	}
	return artifact, nil
}

func (s *Service) protectedReadSnapshot(ctx context.Context, token, project, id string) (Object, error) {
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return nil, e
	}
	defer tx.Rollback()
	p, e := authenticate(tx, token)
	if e != nil {
		return nil, e
	}
	if !protectedAllowed(p, project) {
		return nil, Fail(404, "NOT_FOUND", "artifact unavailable")
	}
	artifact, e := s.readObject(tx, p, project, "Artifact", id)
	if e != nil {
		return nil, e
	}
	if artifact["access_class"] != "VERIFIER_ONLY" {
		return nil, Fail(422, "GATE_FAILED", "protected artifact required")
	}
	if e = s.effective(tx, project, Ref(artifact, "Artifact")); e != nil {
		return nil, e
	}
	return artifact, nil
}
func (s *Service) ReadProtectedArtifact(ctx context.Context, token, project, id string) (Object, []byte, error) {
	artifact, e := s.protectedReadSnapshot(ctx, token, project, id)
	if e != nil {
		return nil, nil, e
	}
	mode := Str(artifact, "measurement_mode")
	if e = s.protectedReady(ctx, mode); e != nil {
		return nil, nil, e
	}
	size, e := Num(artifact, "byte_size")
	if e != nil {
		return nil, nil, e
	}
	descriptor := protectedstore.Blob{Ticket: Str(artifact, "storage_key"), Project: project, Hash: Str(artifact, "content_hash"), Size: size, MediaType: Str(artifact, "media_type"), MeasurementMode: mode}
	if !descriptor.Valid() {
		return nil, nil, protectedFailure(protectedstore.ErrIntegrity)
	}
	raw, e := s.Protected.Read(ctx, descriptor)
	if e != nil {
		return nil, nil, protectedFailure(e)
	}
	if Digest(raw) != descriptor.Hash || int64(len(raw)) != descriptor.Size {
		return nil, nil, protectedFailure(protectedstore.ErrIntegrity)
	}
	if e = s.protectedReady(ctx, mode); e != nil {
		return nil, nil, e
	}
	current, e := s.protectedReadSnapshot(ctx, token, project, id)
	if e != nil {
		return nil, nil, e
	}
	if Hash(current) != Hash(artifact) {
		return nil, nil, Fail(412, "STALE_INPUT", "protected artifact changed during read")
	}
	return current, raw, nil
}

func (s *Service) protectedContent(w http.ResponseWriter, r *http.Request, tx *sql.Tx, project, id, cid string) {
	tx.Rollback() // End the outer HTTP snapshot before provider IO and fresh auth.
	artifact, raw, e := s.ReadProtectedArtifact(r.Context(), strings.TrimPrefix(r.Header.Get("Authorization"), "Bearer "), project, id)
	if e != nil {
		s.writeError(w, cid, e)
		return
	}
	hash, e := hex.DecodeString(strings.TrimPrefix(Str(artifact, "content_hash"), "sha256:"))
	if e != nil || len(hash) != 32 {
		s.writeError(w, cid, protectedFailure(protectedstore.ErrIntegrity))
		return
	}
	tag, e := ETag(artifact)
	if e != nil {
		s.writeError(w, cid, e)
		return
	}
	w.Header().Set("Content-Type", Str(artifact, "media_type"))
	w.Header().Set("Digest", "sha-256="+base64.StdEncoding.EncodeToString(hash))
	w.Header().Set("Content-Disposition", "attachment")
	w.Header().Set("Content-Security-Policy", "sandbox; default-src 'none'")
	w.Header().Set("X-Content-Type-Options", "nosniff")
	w.Header().Set("Cache-Control", "no-store")
	w.Header().Set("ETag", tag)
	w.Write(raw)
}
