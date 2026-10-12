//go:build windows

package host

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"strings"
	"time"

	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/verifier"
)

// The managed producer is a privileged Desktop/main-process operation. This
// request file is not a renderer RPC, new native frame, or provider.probe side
// effect. The consumer must own the existing control data-root lease.
func LoadLocalRuntimeQualificationRequest(path string) (domain.LocalRuntimeQualificationRequest, error) {
	var request domain.LocalRuntimeQualificationRequest
	raw, e := readRuntimeManagedFile(path, 64<<10)
	if e != nil {
		return request, e
	}
	e = decodeRuntimeManaged(raw, &request)
	return request, e
}

type runtimeVerifierRegistration struct {
	Schema         string                      `json:"schema"`
	OwnerHost      string                      `json:"owner_host"`
	OwnerPrincipal string                      `json:"owner_principal"`
	ServiceRoot    string                      `json:"service_root"`
	InstallHash    string                      `json:"installation_hash"`
	Installation   RuntimeVerifierInstallation `json:"installation"`
}

func (h *Host) ensureRuntimeVerifier(ctx context.Context, owner, project string, install RuntimeVerifierInstallation) (string, string, error) {
	if _, e := h.ConfigurationMetadata(ctx, owner, "", nil); e != nil {
		return "", "", e
	}
	root := "local-verifier-root-" + strings.TrimPrefix(domain.Hash([]any{h.InstanceID(), verifier.ServiceID}), "sha256:")[:24]
	child := "local-verifier-" + strings.TrimPrefix(domain.Hash([]any{root, project}), "sha256:")[:32]
	record := runtimeVerifierRegistration{Schema: "researchos.runtime-verifier-registration.v1", OwnerHost: h.InstanceID(), OwnerPrincipal: owner, ServiceRoot: root, InstallHash: domain.Hash(install), Installation: install}
	path := filepath.Join(h.dir, "runtime-verifier-installation.json")
	if raw, e := os.ReadFile(path); e == nil {
		var old runtimeVerifierRegistration
		if json.Unmarshal(raw, &old) != nil || domain.Hash(old) != domain.Hash(record) {
			return "", "", errors.New("registered verifier installation changed; explicit administrator replacement required")
		}
	} else if !os.IsNotExist(e) {
		return "", "", e
	}
	// The service root has no project grants and is never issued a credential.
	// The project child has only VERIFIER; no executor, scheduler or Owner role.
	for _, spec := range []domain.Principal{{ID: root, Roles: []string{"VERIFIER"}, Grants: []domain.Grant{}}, {ID: child, Roles: []string{"VERIFIER"}, Grants: []domain.Grant{{ProjectID: project}}}} {
		var roles string
		var revoked, create int
		e := h.db.QueryRowContext(ctx, `SELECT roles,revoked,can_create_project FROM auth_principals WHERE id=?`, spec.ID).Scan(&roles, &revoked, &create)
		if e == sql.ErrNoRows {
			if e = h.domain.ProvisionPrincipal(ctx, spec); e != nil {
				return "", "", e
			}
			continue
		}
		if e != nil || revoked != 0 || create != 0 || roles != string(domain.Bytes(spec.Roles)) {
			return "", "", errors.New("verifier principal is revoked or changed")
		}
		rows, e := h.db.QueryContext(ctx, `SELECT project,task,run,restricted FROM auth_grants WHERE principal=?`, spec.ID)
		if e != nil {
			return "", "", e
		}
		grants := []domain.Grant{}
		for rows.Next() {
			var g domain.Grant
			if e = rows.Scan(&g.ProjectID, &g.TaskID, &g.RunID, &g.Restricted); e != nil {
				rows.Close()
				return "", "", e
			}
			grants = append(grants, g)
		}
		e = rows.Err()
		rows.Close()
		if e != nil || domain.Hash(grants) != domain.Hash(spec.Grants) {
			return "", "", errors.New("verifier project grant changed")
		}
	}
	var currentRoot string
	var parent sql.NullString
	e := h.db.QueryRowContext(ctx, `SELECT root,parent FROM orchestration_identity WHERE principal=?`, child).Scan(&currentRoot, &parent)
	if e == sql.ErrNoRows {
		e = h.domain.RegisterExecutionIdentity(ctx, child, root)
	} else if e == nil && (currentRoot != root || !parent.Valid || parent.String != root) {
		e = errors.New("verifier identity lineage changed")
	}
	if e != nil {
		return "", "", e
	}
	var rootParent sql.NullString
	if e = h.db.QueryRowContext(ctx, `SELECT root,parent FROM orchestration_identity WHERE principal=?`, root).Scan(&currentRoot, &rootParent); e != nil || currentRoot != root || rootParent.Valid {
		return "", "", errors.New("explicit independent service root missing")
	}
	var ownerRoot string
	if e = h.db.QueryRowContext(ctx, `SELECT root FROM orchestration_identity WHERE principal=?`, owner).Scan(&ownerRoot); e != nil || ownerRoot == root {
		return "", "", errors.New("service authority must differ from registered Owner lineage")
	}
	if e = writePrivate(h.dir, "runtime-verifier-installation.json", record); e != nil {
		return "", "", e
	}
	return root, child, nil
}

// QualifyLocalRuntime performs an explicitly requested managed operation. The
// coordinator remains the sole launcher; this administrative host has no model
// client. Separate verifier credentials never enter the coordinator or worker.
func (h *Host) QualifyLocalRuntime(ctx context.Context, service *domain.Service, coordinator *domain.RuntimeCoordinator, apiURL string, request domain.LocalRuntimeQualificationRequest, install RuntimeVerifierInstallation) (domain.Object, error) {
	if _, e := h.reverify(); e != nil {
		return nil, e
	}
	owner := h.boundPrincipal()
	if owner == "" {
		return nil, errors.New("managed qualification requires existing OS-bound Owner")
	}
	if _, e := h.ConfigurationMetadata(ctx, owner, "", nil); e != nil {
		return nil, e
	}
	ownerToken, e := service.IssueCredential(ctx, owner, 5*time.Minute)
	if e != nil {
		return nil, e
	}
	defer h.revokeCredentialByHash(context.Background(), owner, domain.Digest([]byte(ownerToken)))
	if e = coordinator.ValidateLocalQualification(ctx, ownerToken, request); e != nil {
		return nil, e
	}
	process, e := startRuntimeVerifier(ctx, install)
	if e != nil {
		return nil, e
	}
	defer process.close()
	root, principal, e := h.ensureRuntimeVerifier(ctx, owner, request.ProjectID, install)
	if e != nil {
		return nil, e
	}
	provenance := domain.Object{"schema": "researchos.local-runtime-administration.v1", "action": "EXPLICIT_QUALIFICATION_REQUEST", "request": request, "request_hash": domain.Hash(request), "installation": install, "installation_hash": domain.Hash(install), "service_root": root, "verifier_principal": principal, "process_identity": process.identity, "handshake_nonce": process.nonce, "owner": owner, "owner_host": h.InstanceID(), "os_principal_ref": h.identity.Ref, "application_separation": true, "protected_holdout": false}
	proof, e := service.RecordLocalRuntimeAdministration(ctx, ownerToken, request.ProjectID, provenance)
	if e != nil {
		return nil, e
	}
	run, e := coordinator.ExecuteLocalQualification(ctx, ownerToken, request)
	if e != nil {
		return domain.Object{"administration_ref": domain.Ref(proof, "Artifact"), "run": run, "state": "QUALIFICATION_NOT_ACCEPTED"}, e
	}
	review, e := service.LocalQualificationReview(ctx, ownerToken, request, domain.Str(run, "id"))
	if e != nil {
		return nil, e
	}
	// Issue only after execution is settled. The child process is still the same
	// verified PID/image/creation identity; it alone receives the short token.
	token, e := service.IssueCredential(ctx, principal, 2*time.Minute)
	if e != nil {
		return nil, e
	}
	defer h.revokeCredentialByHash(context.Background(), principal, domain.Digest([]byte(token)))
	epoch, _ := domain.Num(review, "epoch")
	job := verifier.Job{APIURL: apiURL, Token: token, PrincipalID: principal, ServiceRoot: root, ProjectID: request.ProjectID, RuntimeID: request.RuntimeID, TaskRef: review["task_ref"].(map[string]any), RunRef: review["run_ref"].(map[string]any), ProfileRef: review["profile_ref"].(map[string]any), ObservationRef: review["observation_ref"].(map[string]any), PlanHash: domain.Str(review, "plan_hash"), ExecutorID: domain.Str(review, "executor_id"), Epoch: epoch}
	job.VerificationSnapshot = review["verification_snapshot"].(map[string]any)
	job.VerificationSnapshotHash = domain.Str(review, "verification_snapshot_hash")
	result, e := process.verify(ctx, job)
	job.Token = ""
	if e != nil {
		return domain.Object{"state": "QUALIFICATION_NOT_ACCEPTED", "check_status": review["diagnostic_status"], "check_reason": review["diagnostic_reason"], "administration_ref": domain.Ref(proof, "Artifact")}, e
	}
	if domain.Str(result.RuntimeRef, "id") != request.RuntimeID {
		return nil, errors.New("verified runtime differs from Owner request")
	}
	// This re-enters the unchanged admission checks, including actual accepted
	// receipt/root/profile evidence. A child stdout claim cannot authorize use.
	expires := time.Now().UTC().Add(time.Duration(request.PurposeSeconds) * time.Second)
	if e = service.AuthorizeRuntimePurpose(ctx, ownerToken, request.ProjectID, request.RuntimeID, "mu_turn", expires); e != nil {
		return nil, e
	}
	completed := domain.Object{"schema": "researchos.local-runtime-administration.v1", "action": "VERIFIED_PURPOSE_AUTHORIZATION", "request_hash": domain.Hash(request), "administration_ref": domain.Ref(proof, "Artifact"), "verifier_process": process.identity, "service_root": root, "verifier_principal": principal, "acceptance_ref": result.AcceptanceRef, "runtime_ref": result.RuntimeRef, "observation_ref": result.ObservationRef, "purpose": "mu_turn", "expires_at": expires.Format(time.RFC3339Nano), "application_separation": true, "protected_holdout": false}
	final, e := service.RecordLocalRuntimeAdministration(ctx, ownerToken, request.ProjectID, completed)
	if e != nil {
		return nil, e
	}
	return domain.Object{"state": "QUALIFIED_PURPOSE_AUTHORIZED", "runtime_ref": result.RuntimeRef, "acceptance_ref": result.AcceptanceRef, "administration_ref": domain.Ref(final, "Artifact"), "purpose": "mu_turn", "protected_holdout": false}, nil
}
