//go:build windows

package domain

import (
	"context"
	"crypto/rand"
	"database/sql"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"researchos.local/research-os/adapters/protectedstore"
	"strings"
)

const releaseFixtureBackupFormat = "RESEARCHOS_R2_FIXTURE_AUTHORITY_BACKUP_V1"

func releaseBackupKeyPath(h Object, operation string) string {
	return filepath.Join(releaseStateRoot(h), "keys", operation+".key")
}

type releaseBackupGuard struct {
	ctx                       context.Context
	s                         *Service
	project, candidate, proof string
	references                string
	count                     int
}

func (g *releaseBackupGuard) refresh(db *sql.DB) error {
	if _, ok := g.s.Protected.(*protectedstore.CanaryStore); !ok {
		return errors.New("R2_BACKUP_FIXTURE_STORE_REQUIRED")
	}
	if e := g.s.protectedReady(g.ctx, "FIXTURE"); e != nil {
		return e
	}
	boundary, e := g.s.Protected.Boundary(g.ctx)
	if e != nil || boundary.Mode != "CANARY_ONLY" || boundary.IndependentIdentity || !boundary.UnrestrictedSameUserCanRead {
		return errors.New("R2_BACKUP_BOUNDARY_CHANGED")
	}
	var hostCopies int
	if e = db.QueryRow("SELECT count(*) FROM uploaded_content WHERE storage_key GLOB 'ps1:*'").Scan(&hostCopies); e != nil || hostCopies != 0 {
		return errors.New("R2_BACKUP_PROTECTED_HOST_COPY")
	}
	artifacts, e := backupObjects(db, "SELECT body FROM domain_versions WHERE kind='Artifact' AND json_extract(body,'$.access_class')!='PROJECT' ORDER BY project,id,revision")
	if e != nil {
		return e
	}
	if len(artifacts) == 0 || (g.references != "" && (g.count != len(artifacts) || g.references != Hash(artifacts))) {
		return errors.New("R2_BACKUP_PROTECTED_REFERENCES_CHANGED")
	}
	g.count, g.references = len(artifacts), Hash(artifacts)
	for _, artifact := range artifacts {
		if e = g.artifact(db, artifact); e != nil {
			return e
		}
	}
	fixture := &Service{DB: db, Contracts: g.s.Contracts, Protected: g.s.Protected}
	tx, e := db.BeginTx(g.ctx, nil)
	if e != nil {
		return e
	}
	defer tx.Rollback()
	x, e := load(tx, g.project, "SystemCandidate", g.candidate)
	if e != nil {
		return e
	}
	_, proof, e := fixture.evolutionHoldoutVerdict(g.ctx, tx, g.project, x)
	if e != nil || proof != g.proof {
		return errors.New("R2_BACKUP_PRIVATE_PROOF_CHANGED")
	}
	return nil
}

func (g *releaseBackupGuard) artifact(db *sql.DB, a Object) error {
	project, ticket := Str(a, "project_id"), Str(a, "storage_key")
	if a["access_class"] != "VERIFIER_ONLY" || a["measurement_mode"] != "FIXTURE" || !protectedstore.ValidTicket(ticket) {
		return errors.New("R2_BACKUP_PROTECTED_REFERENCE_INVALID")
	}
	size, e := Num(a, "byte_size")
	if e != nil {
		return e
	}
	expected := protectedstore.Blob{Ticket: ticket, Project: project, Hash: Str(a, "content_hash"), Size: size, MediaType: Str(a, "media_type"), MeasurementMode: "FIXTURE"}
	if !expected.Valid() {
		return errors.New("R2_BACKUP_DESCRIPTOR_INVALID")
	}
	got, e := g.s.Protected.Describe(g.ctx, project, ticket)
	if e != nil || got != expected {
		return errors.New("R2_BACKUP_DESCRIPTOR_CHANGED")
	}
	raw, e := g.s.Protected.Read(g.ctx, expected)
	if e != nil || Digest(raw) != expected.Hash || int64(len(raw)) != expected.Size {
		return errors.New("R2_BACKUP_PROTECTED_BODY_CHANGED")
	}
	var copies int
	if e = db.QueryRow("SELECT count(*) FROM uploaded_content WHERE storage_key=?", ticket).Scan(&copies); e != nil || copies != 0 {
		return errors.New("R2_BACKUP_PROTECTED_HOST_COPY")
	}
	return nil
}

func (s *Service) releaseBackupPolicy(ctx context.Context, project, candidate, operation, proof string) (*backupPolicy, error) {
	g := &releaseBackupGuard{ctx: ctx, s: s, project: project, candidate: candidate, proof: proof}
	if e := g.refresh(s.DB); e != nil {
		return nil, e
	}
	purpose := Object{"kind": "R2_FIXTURE_SAME_HOST_RELEASE", "operation": operation, "project": project,
		"candidate": candidate, "private_proof_hash": proof, "protected_reference_digest": g.references,
		"protected_reference_versions": g.count, "protected_payloads_included": false,
		"recovery_dependency": "ORIGINAL_CANARY_STORE", "scope": "FIXTURE_ONLY"}
	return &backupPolicy{format: releaseFixtureBackupFormat, databaseName: "researchos.sqlite", purpose: purpose,
		validate: g.refresh, allowProtected: g.artifact}, nil
}

func (s *Service) writeReleaseAuthorityBackup(ctx context.Context, h Object, project, candidate, operation, proof string) (string, error) {
	policy, e := s.releaseBackupPolicy(ctx, project, candidate, operation, proof)
	if e != nil {
		return "", e
	}
	keyPath := releaseBackupKeyPath(h, operation)
	if key, readErr := os.ReadFile(keyPath); readErr == nil {
		manifest, _, readErr := readBackupPolicy(releaseBackupPath(h, operation), key, policy)
		if readErr != nil {
			return "", readErr
		}
		hash := strings.TrimPrefix(Digest(Bytes(manifest)), "sha256:")
		if readErr = s.verifyReleaseAuthorityBackup(ctx, h, project, candidate, operation, proof, hash); readErr != nil {
			return "", readErr
		}
		return hash, nil
	} else if !os.IsNotExist(readErr) {
		return "", readErr
	}
	key := make([]byte, 32)
	if _, e = rand.Read(key); e != nil {
		return "", e
	}
	if e = os.MkdirAll(filepath.Dir(keyPath), 0700); e != nil {
		return "", e
	}
	if e = backupWrite(keyPath, key); e != nil {
		return "", e
	}
	dir := releaseBackupPath(h, operation)
	manifest, e := s.createBackupPolicy(ctx, dir, key, policy)
	if e != nil {
		return "", e
	}
	// A backup qualifies only if the actual encrypted authority can restore into
	// a separate directory while every external protected reference still resolves.
	if e = s.verifyReleaseAuthorityBackup(ctx, h, project, candidate, operation, proof, strings.TrimPrefix(Digest(Bytes(manifest)), "sha256:")); e != nil {
		return "", e
	}
	return strings.TrimPrefix(Digest(Bytes(manifest)), "sha256:"), nil
}

func (s *Service) verifyReleaseAuthorityBackup(ctx context.Context, h Object, project, candidate, operation, proof, expected string) error {
	if !validReleaseOperationID(operation) {
		return errors.New("R2_BACKUP_OPERATION_INVALID")
	}
	key, e := os.ReadFile(releaseBackupKeyPath(h, operation))
	if e != nil {
		return e
	}
	policy, e := s.releaseBackupPolicy(ctx, project, candidate, operation, proof)
	if e != nil {
		return e
	}
	manifest, _, e := readBackupPolicy(releaseBackupPath(h, operation), key, policy)
	if e != nil {
		return e
	}
	if strings.TrimPrefix(Digest(Bytes(manifest)), "sha256:") != expected {
		return errors.New("R2_BACKUP_MANIFEST_CHANGED")
	}
	parent := filepath.Join(releaseStateRoot(h), "restore-verifications")
	if e = os.MkdirAll(parent, 0700); e != nil {
		return e
	}
	dest := filepath.Join(parent, operation+"-"+ID())
	defer func() { _ = os.RemoveAll(dest) }()
	versions, e := backupMigrations(s.DB)
	if e != nil {
		return e
	}
	report, e := restoreBackupPolicy(ctx, releaseBackupPath(h, operation), dest, RestoreOptions{Key: key, SupportedMigrations: versions, Contracts: s.Contracts}, policy)
	if e != nil {
		return e
	}
	if report.Status != "RESTORED_RECONCILIATION_REQUIRED" {
		return fmt.Errorf("R2_BACKUP_RESTORE_STATUS: %s", report.Status)
	}
	return nil
}
