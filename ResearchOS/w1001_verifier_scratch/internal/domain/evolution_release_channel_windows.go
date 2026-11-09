//go:build windows

package domain

import (
	"context"
	"encoding/json"
	"errors"
	"path/filepath"
	"researchos.local/research-os/adapters/protectedstore"
	"researchos.local/research-os/ops/supervisor"
)

// HandleReleaseFixture is reachable only through control's inherited private
// capability. The host supplies its journal view; control never opens its lock.
func (s *Service) HandleReleaseFixture(ctx context.Context, kind, root string, m supervisor.ReleasePrivateMessage) (supervisor.ReleasePrivateMessage, error) {
	var out supervisor.ReleasePrivateMessage
	if _, ok := s.Protected.(*protectedstore.CanaryStore); !ok {
		return out, errors.New("private FIXTURE store required")
	}
	if m.Snapshot == nil || m.Snapshot.Data != root {
		return out, errors.New("host snapshot root changed")
	}
	state := *m.Snapshot
	switch kind {
	case "FIXTURE_SEAL":
		var request Object
		if e := json.Unmarshal(m.Request, &request); e != nil {
			return out, e
		}
		a, e := s.sealEvolutionReleaseFixture(ctx, m.Project, m.Candidate, request, &state)
		out.Admission = &a
		return out, e
	case "FIXTURE_CURRENT", "FIXTURE_DISPATCH", "FIXTURE_CUTOVER":
		if m.Admission == nil {
			return out, errors.New("sealed admission missing")
		}
		a := *m.Admission
		if e := s.releaseAdmissionCurrent(ctx, a); e != nil {
			return out, e
		}
		if state.Active != a.StableSHA256 || (state.Epoch != a.ExpectedEpoch && state.Epoch != a.ExpectedEpoch+1) {
			return out, errors.New("host slot no longer stable")
		}
		if kind == "FIXTURE_DISPATCH" {
			if state.Phase != "PREPARED" || state.Operation != a.Operation || state.Admission != releasePlainDigest(a) {
				return out, errors.New("host prepare fence missing")
			}
			if e := releaseOperationCAS(s.DB, a.Operation, "PREPARED", "DISPATCHED", ""); e != nil {
				return out, e
			}
		}
		if kind == "FIXTURE_CUTOVER" {
			b, e := s.writeReleaseCutover(ctx, root, state, a)
			out.Cutover = b
			return out, e
		}
		return out, nil
	case "FIXTURE_PROJECT":
		return s.projectReleasePrivate(ctx, state, m)
	default:
		return out, errors.New("unknown private fixture release command")
	}
}

func (s *Service) projectReleasePrivate(ctx context.Context, state supervisor.ReleaseState, m supervisor.ReleasePrivateMessage) (supervisor.ReleasePrivateMessage, error) {
	var out supervisor.ReleasePrivateMessage
	if m.Observation == nil || state.AdmissionBundle == nil {
		return out, errors.New("host receipt missing")
	}
	r := *m.Observation
	a := *state.AdmissionBundle
	if state.Phase != "CANARY" || state.Operation != a.Operation || state.Admission != releasePlainDigest(a) || r.Operation != state.Operation || r.Epoch != state.Epoch || r.ActiveSHA256 != state.Active || r.CandidateSHA256 != a.CandidateSHA256 || r.LastGoodSHA256 != a.StableSHA256 || r.PID != state.PID || r.CreatedNS != state.CreatedNS || r.ImageSHA256 != state.ImageSHA256 || !r.ProcessAlive || r.JournalHash == "" || r.Sequence == 0 {
		return out, errors.New("host receipt snapshot differs")
	}
	// Exact receipt bytes are canonical JSON from the host's immutable record.
	receipt := releasePlainDigest(r)
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return out, e
	}
	defer tx.Rollback()
	o, e := readReleaseOperationTx(tx, a.Project, a.Operation)
	if e != nil {
		return out, e
	}
	if o.Status == "PROJECTED" && o.Receipt.String == receipt {
		out.Result = Bytes(Object{"status": "PROJECTED", "receipt_digest": receipt, "projection_revision": o.Revision})
		return out, nil
	}
	if o.Status != "DISPATCHED" || o.Admission != state.Admission || o.Epoch+1 != state.Epoch {
		return out, errors.New("operation not dispatched under host epoch")
	}
	x, e := load(tx, a.Project, "SystemCandidate", a.CandidateID)
	if e != nil {
		return out, e
	}
	if x["status"] != "EVALUATING" || x["regression_acceptance_id"] != a.AcceptanceID {
		return out, errors.New("candidate changed before private projection")
	}
	h, e := s.evolutionCurrent(tx, a.Project, x)
	if e != nil {
		return out, e
	}
	if filepath.Clean(releaseFixtureData(h)) != filepath.Clean(state.Data) {
		return out, errors.New("projection authority root changed")
	}
	accepted, e := load(tx, a.Project, "AcceptanceReceipt", a.AcceptanceID)
	if e != nil {
		return out, e
	}
	if e = s.releaseActorsCurrent(tx, a.Project, x, h, accepted); e != nil {
		return out, e
	}
	res, e := tx.Exec(`UPDATE evolution_slots SET active_hash=?,candidate=?,epoch=?,state='CANARY' WHERE project=? AND state='STABLE' AND epoch=? AND active_hash=?`, "sha256:"+a.CandidateSHA256, a.CandidateID, state.Epoch, a.Project, a.ExpectedEpoch, "sha256:"+a.StableSHA256)
	if e != nil {
		return out, e
	}
	n, e := res.RowsAffected()
	if e != nil || n != 1 {
		return out, errors.New("private slot projection fence changed")
	}
	x["status"] = "CANARY"
	if e = bump(x); e != nil {
		return out, e
	}
	if e = s.put(tx, "SystemCandidate", x); e != nil {
		return out, e
	}
	res, e = tx.Exec(`UPDATE evolution_release_operations SET status='OBSERVED',receipt_digest=? WHERE operation_id=? AND status='DISPATCHED' AND admission_hash=?`, receipt, a.Operation, state.Admission)
	if e != nil {
		return out, e
	}
	n, e = res.RowsAffected()
	if e != nil || n != 1 {
		return out, errors.New("private receipt observation fence changed")
	}
	res, e = tx.Exec(`UPDATE evolution_release_operations SET status='PROJECTED',projection_revision=? WHERE operation_id=? AND status='OBSERVED' AND receipt_digest=?`, x["revision"], a.Operation, receipt)
	if e != nil {
		return out, e
	}
	n, e = res.RowsAffected()
	if e != nil || n != 1 {
		return out, errors.New("private operation projection fence changed")
	}
	if e = s.event(tx, a.Project, "SystemCandidate", x, Str(h, "release_principal"), ID(), "PROJECT_UPDATED"); e != nil {
		return out, e
	}
	if e = tx.Commit(); e != nil {
		return out, e
	}
	out.Result = Bytes(Object{"status": "PROJECTED", "operation_id": a.Operation, "receipt_digest": receipt, "projection_revision": x["revision"], "candidate_status": x["status"], "scope": "R2_NATIVE_FIXTURE"})
	return out, nil
}
