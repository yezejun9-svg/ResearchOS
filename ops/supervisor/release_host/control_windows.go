//go:build windows

package main

import (
	"bufio"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	rt "researchos.local/research-os/adapters/runtime"
	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/ops/supervisor"
	"time"
)

type command struct {
	Action        string          `json:"action"`
	Project       string          `json:"project"`
	Candidate     string          `json:"candidate"`
	CandidatePath string          `json:"candidate_path"`
	Operation     string          `json:"operation"`
	Request       json.RawMessage `json:"request"`
}

func runControlHost(control, root, work, web, listen, private, contracts string) error {
	if !filepath.IsAbs(root) || !filepath.IsAbs(control) || !filepath.IsAbs(work) || !filepath.IsAbs(web) || !filepath.IsAbs(private) || contracts == "" || listen == "" {
		return errors.New("absolute actual-control fixture host bindings required")
	}
	j, e := supervisor.OpenReleaseJournal(filepath.Join(root, "release-state"))
	if e != nil {
		return e
	}
	defer j.Close()
	d := &supervisor.ControlFixtureDriver{Journal: j, WorkDir: work, WebDir: web, Listen: listen, FixtureStore: private, Output: os.Stderr}
	d.RestoreWithContext = func(ctx context.Context, s supervisor.ReleaseState, lease *rt.DataRootLease) (supervisor.ReleaseRestoreResult, error) {
		return domain.RestoreEvolutionCutoverContext(ctx, s, lease, contracts, private)
	}
	verify := func(a supervisor.ReleaseAdmission) error {
		state := j.State()
		_, e := d.Private(context.Background(), "FIXTURE_CURRENT", supervisor.ReleasePrivateMessage{Admission: &a, Snapshot: &state})
		return e
	}
	engine, e := supervisor.NewReleaseEngine(j, d, d, verify)
	if e != nil {
		return e
	}
	if j.Sequence() == 0 {
		ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
		e = engine.BootstrapFixture(ctx, control, filepath.Join(root, "data"))
		cancel()
		if e != nil {
			return e
		}
	}
	encoder := json.NewEncoder(os.Stdout)
	if e = encoder.Encode(map[string]any{"status": "HOST_READY", "state": j.State(), "recovered": j.State().Phase != "STABLE"}); e != nil {
		return e
	}
	scan := bufio.NewScanner(os.Stdin)
	scan.Buffer(make([]byte, 1024), 8192)
	for scan.Scan() {
		var c command
		if e = json.Unmarshal(scan.Bytes(), &c); e != nil {
			return e
		}
		ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
		result, err := controlCommand(ctx, c, root, j, d, engine)
		cancel()
		reply := map[string]any{"action": c.Action, "state": j.State(), "result": result}
		if err != nil {
			reply["error"] = err.Error()
		}
		if e = encoder.Encode(reply); e != nil {
			return e
		}
		if c.Action == "stop" && err == nil {
			return nil
		}
	}
	// EOF releases only the host journal. It does not repeat stop or launch.
	return scan.Err()
}

func controlCommand(ctx context.Context, c command, root string, j *supervisor.ReleaseJournal, d *supervisor.ControlFixtureDriver, engine *supervisor.ReleaseEngine) (any, error) {
	state := j.State()
	switch c.Action {
	case "status":
		return engine.Reconcile()
	case "seal":
		if state.Phase != "STABLE" {
			return nil, errors.New("stable host required to seal")
		}
		return d.Private(ctx, "FIXTURE_SEAL", supervisor.ReleasePrivateMessage{Project: c.Project, Candidate: c.Candidate, Request: c.Request, Snapshot: &state})
	case "execute":
		// CANARY is an observation/projection retry only; no switch is dispatched.
		if state.Phase == "STABLE" {
			if len(c.Operation) != 64 || filepath.Base(c.Operation) != c.Operation {
				return nil, errors.New("sealed operation identifier required")
			}
			raw, e := os.ReadFile(filepath.Join(root, "release-state", "admissions", c.Operation+".json"))
			if e != nil {
				return nil, e
			}
			var a supervisor.ReleaseAdmission
			if e = json.Unmarshal(raw, &a); e != nil {
				return nil, e
			}
			if a.Operation != c.Operation {
				return nil, errors.New("sealed operation mismatch")
			}
			state, e = engine.PrepareFixture(a, c.CandidatePath)
			if e != nil {
				return nil, e
			}
		}
		if state.Operation != c.Operation {
			return nil, errors.New("current host operation differs")
		}
		if state.Phase == "PREPARED" {
			if _, e := d.Private(ctx, "FIXTURE_DISPATCH", supervisor.ReleasePrivateMessage{Snapshot: &state, Admission: state.AdmissionBundle}); e != nil {
				return nil, e
			}
			var e error
			state, e = engine.SwitchFixture(ctx, c.Operation)
			if e != nil {
				return nil, e
			}
		} else if state.Phase != "CANARY" {
			return nil, errors.New("release outcome unknown; journal inspection only")
		}
		receipt, _, e := supervisor.WriteFixtureReceipt(filepath.Join(root, "release-state"), j, d)
		if e != nil {
			return nil, e
		}
		return d.Private(ctx, "FIXTURE_PROJECT", supervisor.ReleasePrivateMessage{Snapshot: &state, Observation: &receipt})
	case "rollback":
		return engine.RollbackFixture(ctx, c.Operation)
	case "stop":
		return nil, d.ShutdownFixture(ctx)
	default:
		return nil, fmt.Errorf("unknown bounded host command %q", c.Action)
	}
}
