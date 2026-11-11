//go:build windows

package domain

import (
	"bytes"
	"context"
	"database/sql"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	rt "researchos.local/research-os/adapters/runtime"
	"researchos.local/research-os/adapters/sources"
	sandbox "researchos.local/research-os/ops/experiment_sandbox"
)

// RuntimeCoordinatorConfig is private host configuration. None of its tokens,
// paths or command bindings are serialized into the sandbox request.
type RuntimeCoordinatorConfig struct {
	HarnessDriver          rt.CodexDriver                                              `json:"-"`
	HarnessAuthority       HarnessAuthority                                            `json:"-"`
	DataRoot               string                                                      `json:"data_root"`
	APIURL                 string                                                      `json:"api_url"`
	SchedulerToken         string                                                      `json:"scheduler_token"`
	Routes                 []RuntimeCoordinatorRoute                                   `json:"routes"`
	Providers              []RuntimeProviderRoute                                      `json:"providers"`
	WorkspaceAuthority     WorkspaceAuthority                                          `json:"-"`
	ConfigurationAuthority ClientConfigurationAuthority                                `json:"-"`
	ModelCredential        func(context.Context, RuntimeProviderRoute) ([]byte, error) `json:"-"`
	ClientSchema           *SchemaDoc                                                  `json:"-"`
	RunTool                func(context.Context, RuntimeToolRequest) (Object, error)   `json:"-"`
	// PrepareLocalRuntime performs offline reconciliation only, under the sole scan lease.
	PrepareLocalRuntime func(context.Context, *RuntimeCoordinator) error `json:"-"`
	// A managed startup request cannot race an ordinary Scan before its fence.
	ManagedStartupHold bool `json:"-"`
}
type RuntimeCoordinatorRoute struct {
	ProjectID     string `json:"project_id"`
	RuntimeID     string `json:"runtime_id"`
	ExecutorID    string `json:"executor_id"`
	ExecutorToken string `json:"executor_token"`
	CommandID     string `json:"command_id"`
	Executable    string `json:"executable"`
	BundleFile    string `json:"bundle_file,omitempty"`
}
type RuntimeCoordinator struct {
	harnessMu            sync.Mutex
	harnessRoutes        map[string]harnessRoute
	service              *Service
	config               RuntimeCoordinatorConfig
	lock                 *os.File
	borrowed             *rt.DataRootLease
	client               *http.Client
	mu                   sync.Mutex
	scanMu               sync.Mutex
	quiesced             bool
	releaseIntakeClosed  bool
	intakeClosed         atomic.Bool
	startupComplete      bool
	qualificationActive  bool
	qualificationRequest string
	active               map[string]bool
	workers              sync.WaitGroup
	errors               chan error
	boundaryHook         func(string, Object)
	routeMu              sync.RWMutex
	preparedRoutes       map[string]preparedRuntimeRoute
	schedulerCredentials map[string]string
	setupFailures        map[string]string
	// Offline tests only; deliberately absent from serialized host configuration.
	sourceFixtureAdapter func(Object) sources.Adapter
}

// boundary is an internal observation seam for process-crash verification; it
// cannot be configured through HTTP, task metadata or host configuration JSON.
func (c *RuntimeCoordinator) boundary(name string, fact Object) {
	if c.boundaryHook != nil {
		c.boundaryHook(name, fact)
	}
}

func (s *Service) NewRuntimeCoordinator(ctx context.Context, config RuntimeCoordinatorConfig) (*RuntimeCoordinator, error) {
	return s.newRuntimeCoordinator(ctx, config, nil)
}

// NewRuntimeCoordinatorWithLease borrows the control process's exclusive
// data-root lease. It cannot be enabled through runtime coordinator JSON.
func (s *Service) NewRuntimeCoordinatorWithLease(ctx context.Context, config RuntimeCoordinatorConfig, lease *rt.DataRootLease) (*RuntimeCoordinator, error) {
	if lease == nil {
		return nil, errors.New("control data-root lease required")
	}
	return s.newRuntimeCoordinator(ctx, config, lease)
}

func (s *Service) newRuntimeCoordinator(ctx context.Context, config RuntimeCoordinatorConfig, lease *rt.DataRootLease) (*RuntimeCoordinator, error) {
	u, e := url.Parse(config.APIURL)
	if e != nil || u.Scheme != "http" || u.User != nil || u.Path != "" || u.RawQuery != "" || u.Fragment != "" || net.ParseIP(u.Hostname()) == nil || !net.ParseIP(u.Hostname()).IsLoopback() {
		return nil, errors.New("loopback control API required")
	}
	root, e := filepath.Abs(config.DataRoot)
	if e != nil {
		return nil, e
	}
	rows, e := s.DB.QueryContext(ctx, "PRAGMA database_list")
	if e != nil {
		return nil, e
	}
	database := ""
	for rows.Next() {
		var seq int
		var name, path string
		if e = rows.Scan(&seq, &name, &path); e != nil {
			rows.Close()
			return nil, e
		}
		if name == "main" {
			database = path
		}
	}
	e = rows.Err()
	rows.Close()
	if e != nil {
		return nil, e
	}
	if database == "" || !strings.EqualFold(filepath.Clean(filepath.Dir(database)), filepath.Clean(root)) {
		return nil, errors.New("coordinator data root differs from database")
	}
	var lock *os.File
	if lease == nil {
		lock, e = rt.LockDataRoot(root)
	} else {
		e = lease.Borrow(root)
	}
	if e != nil {
		return nil, e
	}
	closeOwned := func() {
		if lock != nil {
			_ = lock.Close()
		}
		if lease != nil {
			_ = lease.ReturnBorrow()
		}
	}
	c := &RuntimeCoordinator{service: s, config: config, lock: lock, borrowed: lease, client: &http.Client{Timeout: 10 * time.Second, CheckRedirect: func(*http.Request, []*http.Request) error { return errors.New("control redirect prohibited") }}, active: map[string]bool{}, errors: make(chan error, 16)}
	c.config.DataRoot = root
	// The exclusive data-root lease already belongs to this constructor. Do not
	// publish an open admission guard before restoring durable qualification state.
	c.intakeClosed.Store(true)
	fenced, e := c.managedQualificationUnsettled(ctx)
	if e != nil {
		closeOwned()
		return nil, e
	}
	c.intakeClosed.Store(config.ManagedStartupHold || fenced)
	for _, route := range config.Routes {
		if route.CommandID == "" || !filepath.IsAbs(route.Executable) {
			closeOwned()
			return nil, errors.New("frozen local command binding required")
		}
		if e = c.authority(ctx, route); e != nil {
			closeOwned()
			return nil, e
		}
	}
	if e = os.MkdirAll(filepath.Join(root, "runtime-dispatches"), 0700); e != nil {
		closeOwned()
		return nil, e
	}
	return c, nil
}

func (c *RuntimeCoordinator) authority(ctx context.Context, route RuntimeCoordinatorRoute) error {
	tx, e := c.service.DB.BeginTx(ctx, nil)
	if e != nil {
		return e
	}
	defer tx.Rollback()
	if _, e = resourcePrincipal(tx, c.schedulerCredential(route.ProjectID), route.ProjectID, "SCHEDULER"); e != nil {
		return e
	}
	executor, e := authenticate(tx, route.ExecutorToken)
	if e != nil {
		return e
	}
	if executor.ID != route.ExecutorID || !executor.HasRole("EXECUTOR") {
		return Fail(403, "FORBIDDEN", "bound executor credential required")
	}
	return nil
}

func (c *RuntimeCoordinator) Close() error {
	c.workers.Wait()
	if c.lock != nil {
		return c.lock.Close()
	}
	return c.borrowed.ReturnBorrow()
}

// Serve owns the sole scan over existing READY Task rows. Launch records never
// become another queue, and a process restart never dispatches an old record.
func (c *RuntimeCoordinator) Serve(ctx context.Context, onError func(error)) error {
	c.scanMu.Lock()
	var e error
	if !c.startupComplete {
		if c.quiesced {
			e = errors.New("runtime startup recovery fenced")
		} else {
			e = c.Recover(ctx)
			c.startupComplete = e == nil
			if e != nil {
				c.intakeClosed.Store(true)
			}
		}
	}
	c.scanMu.Unlock()
	if e != nil {
		return e
	}
	tick := time.NewTicker(time.Second)
	defer tick.Stop()
	for {
		if e := c.Scan(ctx); e != nil && onError != nil {
			onError(e)
		}
		select {
		case err := <-c.errors:
			if onError != nil {
				onError(err)
			}
		case <-ctx.Done():
			c.workers.Wait()
			return nil
		case <-tick.C:
		}
	}
}
func (c *RuntimeCoordinator) Scan(ctx context.Context) error {
	c.scanMu.Lock()
	defer c.scanMu.Unlock()
	if c.quiesced || c.qualificationActive || c.config.ManagedStartupHold {
		c.intakeClosed.Store(true)
		return nil
	}
	if fenced, err := c.managedQualificationUnsettled(ctx); err != nil {
		c.intakeClosed.Store(true)
		return err
	} else if fenced {
		c.intakeClosed.Store(true)
		return nil
	}
	var failures []error
	if c.config.PrepareLocalRuntime != nil {
		if e := c.config.PrepareLocalRuntime(ctx, c); e != nil {
			failures = append(failures, e)
		}
	}
	if e := c.projectCurrentSessionRuns(ctx); e != nil {
		failures = append(failures, e)
	}
	if e := c.advanceResearchCycles(ctx); e != nil {
		failures = append(failures, e)
	}
	if e := c.advanceIntentTasks(ctx); e != nil {
		failures = append(failures, e)
	}
	if e := c.scanHarness(ctx); e != nil {
		failures = append(failures, e)
	}
	for _, route := range c.runtimeRoutes() {
		key := route.ProjectID + "/" + route.ExecutorID
		c.mu.Lock()
		busy := c.active[key]
		c.mu.Unlock()
		if busy {
			continue
		}
		if e := c.authority(ctx, route); e != nil {
			failures = append(failures, e)
			continue
		}
		var active int
		if e := c.service.DB.QueryRowContext(ctx, "SELECT count(*) FROM domain_objects WHERE project=? AND kind='Run' AND json_extract(body,'$.executor_principal_id')=? AND json_extract(body,'$.status') NOT IN ('SETTLED','FAILED','CANCELLED')", route.ProjectID, route.ExecutorID).Scan(&active); e != nil {
			failures = append(failures, e)
			continue
		}
		if active != 0 {
			continue
		}
		rows, e := c.service.DB.QueryContext(ctx, "SELECT body FROM domain_objects WHERE project=? AND kind='Task' AND json_extract(body,'$.status')='READY' AND json_extract(body,'$.task_type') NOT IN ('runtime_qualification','harness_turn') ORDER BY rowid", route.ProjectID)
		if e != nil {
			failures = append(failures, e)
			continue
		}
		candidates := []Object{}
		for rows.Next() {
			var raw string
			if e = rows.Scan(&raw); e != nil {
				break
			}
			var task Object
			task, e = Decode([]byte(raw))
			if e != nil {
				break
			}
			candidates = append(candidates, task)
		}
		e = errors.Join(e, rows.Err())
		rows.Close()
		if e != nil {
			failures = append(failures, e)
			continue
		}
		for _, task := range candidates {
			// A current read preflight skips routes with no purpose or executor grant.
			// The public atomic claim repeats every gate after this transaction closes.
			if e = c.claimCandidate(ctx, route, task); e != nil {
				var fault *Fault
				if !errors.As(e, &fault) {
					failures = append(failures, e)
				}
				continue
			}
			tag, e := ETag(task)
			if e != nil {
				failures = append(failures, e)
				continue
			}
			claimKey := ID()
			result, _, e := c.call(ctx, c.schedulerCredential(route.ProjectID), "POST", c.path(route, "/tasks/"+Str(task, "id")+"/claim"), claimKey, tag, Object{"runtime_id": route.RuntimeID, "executor_principal_id": route.ExecutorID, "context_bundle_id": task["context_bundle_id"]})
			if e != nil {
				var fault *Fault
				if errors.As(e, &fault) {
					failures = append(failures, e)
					continue
				}
				// A missing acknowledgement is resolved only by this exact durable key.
				// If no committed reply is visible, this route is fenced until restart or
				// explicit reconciliation; no new claim key is sent from this coordinator.
				result, e = c.claimReply(ctx, route, claimKey)
				if e != nil {
					c.mu.Lock()
					c.active[key] = true
					c.mu.Unlock()
					failures = append(failures, errors.New("claim acknowledgement unknown; route fenced for reconciliation"))
					break
				}
			}
			run, ok := result["run"].(map[string]any)
			if !ok || run["task_id"] != task["id"] || run["runtime_id"] != route.RuntimeID || run["executor_principal_id"] != route.ExecutorID || Str(result, "lease_token") == "" {
				c.mu.Lock()
				c.active[key] = true
				c.mu.Unlock()
				failures = append(failures, errors.New("claim response binding invalid; route fenced"))
				break
			}
			c.boundary("claim_committed", run)
			c.mu.Lock()
			c.active[key] = true
			c.mu.Unlock()
			c.workers.Add(1)
			go func(route RuntimeCoordinatorRoute, run Object, lease, key string) {
				defer c.workers.Done()
				defer func() { c.mu.Lock(); delete(c.active, key); c.mu.Unlock() }()
				if err := c.RunAdmitted(ctx, route, run, lease); err != nil {
					select {
					case c.errors <- err:
					default:
					}
				}
			}(route, run, Str(result, "lease_token"), key)
			break
		}
	}
	return errors.Join(failures...)
}

func (c *RuntimeCoordinator) claimCandidate(ctx context.Context, route RuntimeCoordinatorRoute, task Object) error {
	tx, e := c.service.DB.BeginTx(ctx, nil)
	if e != nil {
		return e
	}
	defer tx.Rollback()
	if task["task_type"] == "mu_turn" {
		if e = c.sessionTaskRoute(tx, route.ProjectID, task, route.RuntimeID); e != nil {
			return e
		}
	}
	runtime, e := load(tx, route.ProjectID, "RuntimeRegistration", route.RuntimeID)
	if e != nil {
		return e
	}
	admission, e := c.service.currentRuntimeAdmission(tx, route.ProjectID, task, runtime, []any{"start"}, "claim")
	if e != nil {
		return e
	}
	profile, _ := admission["profile"].(map[string]any)
	if profile["command_id"] != route.CommandID || !runtimeExecutorAllowed(tx, route.ExecutorID, route.ProjectID, Str(task, "id")) {
		return Fail(403, "FORBIDDEN", "route does not bind this Task")
	}
	return nil
}
func (c *RuntimeCoordinator) claimReply(ctx context.Context, route RuntimeCoordinatorRoute, key string) (Object, error) {
	tx, e := c.service.DB.BeginTx(ctx, nil)
	if e != nil {
		return nil, e
	}
	defer tx.Rollback()
	principal, e := resourcePrincipal(tx, c.schedulerCredential(route.ProjectID), route.ProjectID, "SCHEDULER")
	if e != nil {
		return nil, e
	}
	var raw []byte
	if e = tx.QueryRow("SELECT body FROM idempotency WHERE principal=? AND project=? AND operation='claimTask' AND key=?", principal.ID, route.ProjectID, key).Scan(&raw); e != nil {
		return nil, e
	}
	return Decode(raw)
}

func (c *RuntimeCoordinator) path(route RuntimeCoordinatorRoute, path string) string {
	return "/v1/projects/" + url.PathEscape(route.ProjectID) + path
}

// call never retries a POST after an ambiguous transport outcome.
func (c *RuntimeCoordinator) call(ctx context.Context, token, method, path, key, tag string, body any) (Object, http.Header, error) {
	var raw []byte
	media := "application/json"
	if b, ok := body.([]byte); ok {
		raw = b
		media = "application/octet-stream"
	} else if body != nil {
		raw = Bytes(body)
	}
	req, e := http.NewRequestWithContext(ctx, method, c.config.APIURL+path, bytes.NewReader(raw))
	if e != nil {
		return nil, nil, e
	}
	req.Header.Set("Authorization", "Bearer "+token)
	req.Header.Set("Content-Type", media)
	if key != "" {
		req.Header.Set("Idempotency-Key", key)
	}
	if tag != "" {
		req.Header.Set("If-Match", tag)
	}
	res, e := c.client.Do(req)
	if e != nil {
		return nil, nil, errors.New("control request outcome unknown; query durable state before retry")
	}
	defer res.Body.Close()
	raw, e = io.ReadAll(io.LimitReader(res.Body, 4*1024*1024+1))
	if e != nil || len(raw) > 4*1024*1024 {
		return nil, nil, errors.New("control response incomplete")
	}
	object, e := Decode(raw)
	if e != nil {
		return nil, nil, e
	}
	if res.StatusCode < 200 || res.StatusCode >= 300 {
		return nil, res.Header, Fail(res.StatusCode, "CONTROL_REQUEST_FAILED", fmt.Sprintf("control operation returned %d", res.StatusCode))
	}
	return object, res.Header, nil
}

func runtimeNativeIdentity(id sandbox.Identity) Object {
	return Object{"pid": id.PID, "process_created_ns": strconv.FormatInt(id.Created, 10), "job": id.Job, "appcontainer_sid": id.SID, "profile": id.Profile, "staging_directory": id.StagingDirectory}
}

func (c *RuntimeCoordinator) dispatchGate(ctx context.Context, route RuntimeCoordinatorRoute, runID, lease string, epoch int64) (*sql.Tx, Object, Object, error) {
	tx, e := c.service.DB.BeginTx(ctx, nil)
	if e != nil {
		return nil, nil, nil, e
	}
	fail := func(e error) (*sql.Tx, Object, Object, error) { tx.Rollback(); return nil, nil, nil, e }
	if e = resourceWriteLock(tx); e != nil {
		return fail(e)
	}
	if _, e = resourcePrincipal(tx, c.schedulerCredential(route.ProjectID), route.ProjectID, "SCHEDULER"); e != nil {
		return fail(e)
	}
	executor, e := authenticate(tx, route.ExecutorToken)
	if e != nil {
		return fail(e)
	}
	run, e := currentRun(tx, executor, route.ProjectID, runID)
	if e != nil {
		return fail(e)
	}
	if run["executor_principal_id"] != route.ExecutorID || run["runtime_id"] != route.RuntimeID || runTerminal(run) || run["status"] == "CANCEL_REQUESTED" || run["status"] == "RECONCILING" || run["status"] == "LOST" {
		return fail(Fail(409, "STATE_CONFLICT", "run cannot dispatch"))
	}
	if e = runtimeLease(tx, executor, route.ProjectID, run, Object{"lease_token": lease, "lease_epoch": epoch}); e != nil {
		return fail(e)
	}
	dispatch, e := runtimeDispatch(tx, route.ProjectID, runID, epoch)
	if e != nil {
		return fail(e)
	}
	task, e := load(tx, route.ProjectID, "Task", Str(run, "task_id"))
	if e != nil {
		return fail(e)
	}
	if task["task_type"] == "mu_turn" {
		if e = c.sessionTaskRoute(tx, route.ProjectID, task, route.RuntimeID); e != nil {
			return fail(e)
		}
	}
	admission, e := c.service.currentDispatchAdmission(tx, route.ProjectID, task, run, dispatch, "dispatch")
	if e != nil {
		return fail(e)
	}
	profile := admission["profile"].(map[string]any)
	if profile["command_id"] != route.CommandID {
		return fail(Fail(422, "GATE_FAILED", "host command binding differs from profile"))
	}
	return tx, run, dispatch, nil
}

func (c *RuntimeCoordinator) RunAdmitted(ctx context.Context, route RuntimeCoordinatorRoute, run Object, lease string) error {
	c.boundary("before_launch_fence", run)
	epoch, e := Num(run, "lease_epoch")
	if e != nil {
		return e
	}
	runID := Str(run, "id")
	tx, current, dispatch, e := c.dispatchGate(ctx, route, runID, lease, epoch)
	if e != nil {
		return e
	}
	manifest := dispatch["manifest"].(map[string]any)
	inputs, e := c.inputs(tx, route.ProjectID, current, manifest["admission"].(map[string]any))
	if e != nil {
		tx.Rollback()
		return e
	}
	if e = c.projectSessionRun(tx, route.ProjectID, current, nil); e != nil {
		tx.Rollback()
		return e
	}
	if e = stageRuntimeProgram(route, dispatch, inputs); e != nil {
		tx.Rollback()
		return e
	}
	worker := ID()
	locator := Str(dispatch, "dispatch_key")
	result, e := tx.Exec("UPDATE runtime_dispatches SET state='STARTED',worker=?,journal_locator=?,updated_at=? WHERE project=? AND run=? AND epoch=? AND state='PREPARED' AND worker=''", worker, locator, Now(), route.ProjectID, runID, epoch)
	if e != nil {
		tx.Rollback()
		return e
	}
	n, e := result.RowsAffected()
	if e != nil || n != 1 {
		tx.Rollback()
		return Fail(409, "STATE_CONFLICT", "dispatch already attempted; no relaunch")
	}
	if e = tx.Commit(); e != nil {
		return e
	}
	c.boundary("dispatch_started", run)
	directory := filepath.Join(c.config.DataRoot, "runtime-dispatches", locator)
	bridge, e := rt.StartBridge(ctx, directory, rt.BridgeRequest{WorkerID: worker, Manifest: Bytes(dispatch["manifest"]), ManifestHash: Str(dispatch, "manifest_hash"), Executable: route.Executable, Inputs: inputs, BeforeResume: func(identity sandbox.Identity) error {
		tx, _, fresh, e := c.dispatchGate(ctx, route, runID, lease, epoch)
		if e != nil {
			return e
		}
		defer tx.Rollback()
		if fresh["state"] != "STARTED" || fresh["worker"] != worker || len(fresh["identity"].(map[string]any)) != 0 {
			return Fail(409, "STATE_CONFLICT", "launch identity fence consumed")
		}
		_, e = tx.Exec("UPDATE runtime_dispatches SET identity=?,updated_at=? WHERE project=? AND run=? AND epoch=? AND state='STARTED' AND worker=?", string(Bytes(runtimeNativeIdentity(identity))), Now(), route.ProjectID, runID, epoch, worker)
		if e != nil {
			return e
		}

		installed, e := clientQueueInstalled(tx)
		if e != nil {
			return e
		}
		if installed {
			if _, e = tx.Exec(`UPDATE client_queue_fences SET process_identity=?,revision=revision+1 WHERE project=? AND run_id=? AND runtime_epoch=? AND dispatch_key=? AND manifest_hash=?`, string(Bytes(runtimeNativeIdentity(identity))), route.ProjectID, runID, epoch, fresh["dispatch_key"], fresh["manifest_hash"]); e != nil {
				return e
			}
		}
		if e = tx.Commit(); e != nil {
			return e
		}
		c.boundary("suspended_identity", runtimeNativeIdentity(identity))
		return nil
	}})
	if e != nil {
		c.markUnknown(context.Background(), route.ProjectID, runID, epoch, "launch acknowledgement unavailable")
		return e
	}
	c.boundary("native_started", run)
	child, cancel := context.WithCancel(ctx)
	defer cancel()
	brokerContext, cancelBroker := context.WithCancel(child)
	defer cancelBroker()
	go func() {
		select {
		case <-bridge.Done():
			cancelBroker()
		case <-child.Done():
		}
	}()
	heartbeatDone := make(chan struct{})
	heartbeatError := make(chan error, 1)
	// A committed Owner cancel must stop transport and tools promptly; waiting
	// for the 15-second heartbeat would allow an already cancelled check to run.
	go func() {
		tick := time.NewTicker(200 * time.Millisecond)
		defer tick.Stop()
		for {
			select {
			case <-child.Done():
				return
			case <-bridge.Done():
				return
			case <-tick.C:
				var status string
				var currentEpoch int64
				err := c.service.DB.QueryRowContext(child, "SELECT json_extract(body,'$.status'),json_extract(body,'$.lease_epoch') FROM domain_objects WHERE project=? AND kind='Run' AND id=?", route.ProjectID, runID).Scan(&status, &currentEpoch)
				if err != nil || status == "CANCEL_REQUESTED" || currentEpoch != epoch {
					cancelBroker()
					if !bridge.Read().QueueRequired || err != nil || currentEpoch != epoch {
						bridge.Cancel("canonical run cancellation or epoch ended")
					}
					return
				}
			}
		}
	}()
	var mutation sync.Mutex
	go func() {
		defer close(heartbeatDone)
		tick := time.NewTicker(15 * time.Second)
		defer tick.Stop()
		for {
			mutation.Lock()
			e := c.heartbeat(child, route, runID, lease, epoch, locator, "")
			mutation.Unlock()
			if e != nil {
				heartbeatError <- e
				cancel()
				bridge.Cancel("control lease or authority unavailable")
				return
			}
			if e := bridge.Renew(epoch, 90*time.Second); e != nil {
				heartbeatError <- e
				cancel()
				bridge.Cancel("worker lease expired")
				return
			}
			select {
			case <-child.Done():
				return
			case <-tick.C:
			}
		}
	}()
	protocolError := c.runCommandBridge(child, brokerContext, route, runID, lease, epoch, locator, bridge, &mutation)
	if protocolError != nil {
		bridge.Cancel("protocol reconciliation failed")
	}
	<-bridge.Done()
	if protocolError != nil {
		cancel()
		<-heartbeatDone
		c.markUnknown(context.Background(), route.ProjectID, runID, epoch, "protocol not reconciled")
		return protocolError
	}
	tx, e = c.service.DB.BeginTx(ctx, nil)
	if e == nil {
		e = effectsReconciled(tx, route.ProjectID, runID)
		tx.Rollback()
	}
	if e != nil {
		cancel()
		<-heartbeatDone
		c.markUnknown(context.Background(), route.ProjectID, runID, epoch, "effect reconciliation incomplete")
		return e
	}
	j, e := bridge.Finalize(true)
	if e != nil {
		cancel()
		<-heartbeatDone
		return e
	}
	c.boundary("terminal_durable", run)
	if e = c.ingestObservation(ctx, route.ProjectID, runID, epoch, j); e != nil {
		cancel()
		<-heartbeatDone
		return e
	}
	if j.State == "CANCELLED" {
		cancel()
		<-heartbeatDone
		return c.recoverTerminal(ctx, route.ProjectID, runID, epoch, directory, j)
	}
	if j.State != "SETTLED" && j.State != "FAILED" && j.State != "PAUSED" {
		cancel()
		<-heartbeatDone
		return Fail(409, "STATE_CONFLICT", "worker failed or cancelled")
	}
	observation, e := j.Observation()
	if e != nil {
		cancel()
		<-heartbeatDone
		return e
	}
	if _, e = c.sealOutput(ctx, route, runID, locator+"-host-log", Bytes(observation), j, "LOG"); e != nil {
		cancel()
		<-heartbeatDone
		return e
	}
	if j.State == "PAUSED" {
		cancel()
		<-heartbeatDone
		return nil
	}
	ids := Empty()
	for i, artifact := range j.Artifacts {
		raw, e := os.ReadFile(filepath.Join(directory, "output", artifact.Path))
		if e != nil {
			cancel()
			<-heartbeatDone
			return e
		}
		if Digest(raw) != artifact.Hash || int64(len(raw)) != artifact.Size {
			cancel()
			<-heartbeatDone
			return errors.New("output changed after terminal observation")
		}
		a, e := c.sealOutput(ctx, route, runID, locator+"-"+strconv.Itoa(i), raw, j, "REPORT")
		if e != nil {
			cancel()
			<-heartbeatDone
			return e
		}
		ids = append(ids, a["id"])
		c.boundary("artifact_sealed", a)
	}
	cancel()
	<-heartbeatDone
	select {
	case e := <-heartbeatError:
		return e
	default:
	}
	current, headers, e := c.call(ctx, route.ExecutorToken, "GET", c.path(route, "/runs/"+runID), "", "", nil)
	if e != nil {
		return e
	}
	_, _, e = c.call(ctx, route.ExecutorToken, "POST", c.path(route, "/runs/"+runID+"/report"), locator+"-report", headers.Get("ETag"), Object{"lease_token": lease, "lease_epoch": current["lease_epoch"], "runtime_settled": true, "execution_report": "Host dispatch process, streams, outputs and effects reconciled; independent acceptance required.", "exit_code": j.Receipt.ExitCode, "result_artifact_ids": ids, "checkpoint_artifact_id": current["checkpoint_artifact_id"]})
	if e == nil {
		c.boundary("reported", current)
		tx, err := c.service.DB.BeginTx(ctx, nil)
		if err != nil {
			return err
		}
		defer tx.Rollback()
		latest, err := load(tx, route.ProjectID, "Run", runID)
		if err != nil {
			return err
		}
		if err = c.projectSessionRun(tx, route.ProjectID, latest, ids); err != nil {
			return err
		}
		return tx.Commit()
	}
	return e
}

func (c *RuntimeCoordinator) heartbeat(ctx context.Context, route RuntimeCoordinatorRoute, runID, lease string, epoch int64, external, checkpoint string) error {
	tx, _, _, e := c.dispatchGate(ctx, route, runID, lease, epoch)
	if e != nil {
		return e
	}
	tx.Rollback()
	run, headers, e := c.call(ctx, route.ExecutorToken, "GET", c.path(route, "/runs/"+runID), "", "", nil)
	if e != nil {
		return e
	}
	if checkpoint != "" {
		run["checkpoint_artifact_id"] = checkpoint
	}
	_, _, e = c.call(ctx, route.ExecutorToken, "POST", c.path(route, "/runs/"+runID+"/heartbeat"), ID(), headers.Get("ETag"), Object{"lease_token": lease, "lease_epoch": epoch, "external_run_id": external, "checkpoint_artifact_id": run["checkpoint_artifact_id"]})
	return e
}

func (c *RuntimeCoordinator) inputs(tx *sql.Tx, project string, run, admission Object) (map[string][]byte, error) {
	task, e := load(tx, project, "Task", Str(run, "task_id"))
	if e != nil {
		return nil, e
	}
	bundle, e := load(tx, project, "ContextBundle", Str(run, "context_bundle_id"))
	if e != nil {
		return nil, e
	}
	request := Object{"run_id": run["id"], "task_id": run["task_id"], "task_type": task["task_type"], "task_title": task["title"], "epoch": run["lease_epoch"], "context": bundle, "input_refs": run["input_refs"], "checkpoint_artifact_id": run["checkpoint_artifact_id"]}
	goal, e := load(tx, project, "Goal", Str(task, "goal_id"))
	if e != nil {
		return nil, e
	}
	request["task_description"] = Str(goal, "original_intent")
	if strings.HasPrefix(Str(task, "task_type"), "research_") {
		work, err := loadResearchWork(tx, project, Str(task, "id"))
		if err != nil {
			return nil, err
		}
		request["research_work"] = work.publicParameters()
		if work.Stage == "delivery" {
			cycle, err := load(tx, project, "ResearchCycle", work.Cycle)
			if err != nil {
				return nil, err
			}
			facts, err := c.service.researchCycleFacts(tx, project, cycle, nil)
			if err != nil {
				return nil, err
			}
			request["research_facts"] = facts
		} else if work.Stage == "verification" || work.Stage == "review" {
			snapshot, err := c.service.researchStageSnapshot(tx, project, task)
			if err != nil {
				return nil, err
			}
			request["research_facts"] = snapshot["expected"]
		}
	}
	inputs := map[string][]byte{"request.json": Bytes(request)}
	artifactInputs := Empty()
	for _, v := range Arr(run, "input_refs") {
		ref, ok := v.(map[string]any)
		if !ok {
			return nil, errors.New("invalid input ref")
		}
		if ref["entity_type"] != "Artifact" {
			continue
		}
		artifact, e := load(tx, project, "Artifact", Str(ref, "id"))
		if e != nil {
			return nil, e
		}
		if artifact["access_class"] == "VERIFIER_ONLY" || Hash(Ref(artifact, "Artifact")) != Hash(ref) {
			return nil, Fail(403, "FORBIDDEN", "sandbox input unavailable")
		}
		var raw []byte
		if e = tx.QueryRow("SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=?", project, artifact["storage_key"]).Scan(&raw); e != nil {
			return nil, e
		}
		if Digest(raw) != artifact["content_hash"] {
			return nil, errors.New("input content changed")
		}
		inputs["artifacts/"+Str(artifact, "id")] = raw
		profile, _ := admission["profile"].(map[string]any)
		if profile["backend"] == runtimeMuBackend && Hash(ref) == Hash(admission["profile_ref"]) {
			// The exact host policy remains a sealed dispatch input, but is not
			// user text. Sending its toolchain/path inventory as prompt content
			// would both expose host internals and consume the model body bound.
			continue
		}
		artifactInputs = append(artifactInputs, Object{"id": artifact["id"], "content_hash": artifact["content_hash"], "media_type": artifact["media_type"], "path": "artifacts/" + Str(artifact, "id")})
	}
	if id := Str(run, "checkpoint_artifact_id"); id != "" {
		artifact, use, e := c.service.artifactUse(tx, project, run, id, false)
		if e != nil {
			return nil, e
		}
		if artifact["access_class"] == "VERIFIER_ONLY" {
			return nil, Fail(403, "FORBIDDEN", "protected checkpoint cannot enter runtime")
		}
		var raw []byte
		if e = tx.QueryRow("SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1", project, use["storage_key"]).Scan(&raw); e != nil {
			return nil, e
		}
		if Digest(raw) != artifact["content_hash"] {
			return nil, errors.New("checkpoint bytes changed")
		}
		inputs["checkpoint.json"] = raw
	}
	queued, err := bindClientRunQueue(tx, project, run)
	if err != nil {
		return nil, err
	}
	request["queue_control"] = queued
	if queued {
		var sid, generation string
		if err = tx.QueryRow("SELECT session_id,generation FROM client_queue_fences WHERE project=? AND task_id=?", project, run["task_id"]).Scan(&sid, &generation); err != nil {
			return nil, err
		}
		d, err := runtimeDispatch(tx, project, Str(run, "id"), run["lease_epoch"])
		if err != nil {
			return nil, err
		}
		request["queue_binding"] = Object{"project_id": project, "session_id": sid, "task_id": run["task_id"], "run_id": run["id"], "runtime_epoch": run["lease_epoch"], "queue_generation": generation, "dispatch_key": d["dispatch_key"], "manifest_hash": d["manifest_hash"]}
	}
	request["artifact_inputs"] = artifactInputs
	inputs["request.json"] = Bytes(request)
	return inputs, nil
}

func (c *RuntimeCoordinator) checkpoint(ctx context.Context, route RuntimeCoordinatorRoute, runID, lease string, epoch int64, key string, bridge *rt.Bridge, frame rt.BridgeFrame) (Object, error) {
	payload, e := Decode(frame.Payload)
	if e != nil {
		return nil, Fail(400, "INVALID_REQUEST", "bounded checkpoint object required")
	}
	tx, _, dispatch, e := c.dispatchGate(ctx, route, runID, lease, epoch)
	if e != nil {
		return nil, e
	}
	tx.Rollback()
	if frame.Path != "" && frame.Path != "checkpoint.json" {
		return nil, Fail(403, "FORBIDDEN", "checkpoint cannot select host paths")
	}
	raw := Bytes(payload)
	fact := Object{"project_id": route.ProjectID, "run_id": runID, "epoch": epoch, "manifest_hash": dispatch["manifest_hash"], "dispatch_key": dispatch["dispatch_key"], "sequence": frame.Sequence, "content_hash": Digest(raw), "payload": payload}
	if e = writeRuntimeFact(filepath.Join(bridge.Directory(), "checkpoint-"+strconv.FormatInt(frame.Sequence, 10)+".json"), Bytes(fact)); e != nil {
		return nil, e
	}
	c.boundary("checkpoint_durable", fact)
	a, e := c.sealOutput(ctx, route, runID, key+"-checkpoint-"+strconv.FormatInt(frame.Sequence, 10), raw, bridge.Read(), "CHECKPOINT")
	if e != nil {
		return nil, e
	}
	if e = c.heartbeat(ctx, route, runID, lease, epoch, key, Str(a, "id")); e != nil {
		return nil, e
	}
	return Object{"sequence": frame.Sequence, "type": "checkpoint.sealed", "artifact_ref": Ref(a, "Artifact")}, nil
}

func (c *RuntimeCoordinator) sealOutput(ctx context.Context, route RuntimeCoordinatorRoute, runID, key string, raw []byte, j rt.BridgeJournal, kind string) (Object, error) {
	u, _, e := c.call(ctx, route.ExecutorToken, "POST", c.path(route, "/content"), key+"-upload", "", raw)
	if e != nil {
		return nil, e
	}
	manifest, e := Decode(j.Manifest)
	if e != nil {
		return nil, e
	}
	admission := manifest["admission"].(map[string]any)
	body := Object{"run_id": runID, "kind": kind, "evidence_kind": "GENERATED", "measurement_mode": admission["mode"], "content_hash": u["content_hash"], "storage_key": u["storage_key"], "media_type": "application/octet-stream", "byte_size": len(raw), "input_refs": manifest["input_refs"], "source_refs": Empty(), "produced_by": route.ExecutorID, "access_class": "PROJECT"}
	if permission, _ := admission["permission"].(map[string]any); kind == "REPORT" && (permission["purpose"] == "intent_planning" || strings.HasPrefix(Str(permission, "purpose"), "research_")) {
		if _, err := Decode(raw); err == nil {
			body["media_type"] = "application/json"
		}
	}
	for attempt := 0; attempt < 3; attempt++ {
		_, headers, readErr := c.call(ctx, c.schedulerCredential(route.ProjectID), "GET", c.path(route, "/state"), "", "", nil)
		if readErr != nil {
			return nil, readErr
		}
		a, _, sealErr := c.call(ctx, route.ExecutorToken, "POST", c.path(route, "/artifacts"), key+"-seal", headers.Get("ETag"), body)
		if sealErr == nil {
			return a, nil
		}
		var fault *Fault
		if !errors.As(sealErr, &fault) || fault.Status != http.StatusPreconditionFailed {
			return nil, sealErr
		}
		// A received 412 proves that this mutation did not commit. Only this
		// known rejection permits a fresh state tag; transport ambiguity returns.
		e = sealErr
	}
	return nil, e
}

func (c *RuntimeCoordinator) markUnknown(ctx context.Context, project, run string, epoch int64, reason string) error {
	tx, e := c.service.DB.BeginTx(ctx, nil)
	if e != nil {
		return e
	}
	defer tx.Rollback()
	if e = resourceWriteLock(tx); e != nil {
		return e
	}
	abandoned, e := preparedRunAbandonmentExists(tx, project, run, epoch)
	if e != nil {
		return e
	}
	if abandoned {
		return nil
	}
	if e = unknownClientRunQueue(tx, project, run, reason); e != nil {
		return e
	}
	if _, e = tx.Exec("UPDATE runtime_dispatches SET state='UNKNOWN',reason=?,updated_at=? WHERE project=? AND run=? AND epoch=? AND state!='OBSERVED'", reason, Now(), project, run, epoch); e != nil {
		return e
	}
	current, e := load(tx, project, "Run", run)
	if e != nil {
		return e
	}
	if Hash(current["lease_epoch"]) == Hash(epoch) && !runTerminal(current) {
		if e = c.projectSessionRun(tx, project, current, nil, "Runtime outcome is unconfirmed: "+reason+"; wait for effect and process reconciliation."); e != nil {
			return e
		}
	}
	return tx.Commit()
}
func (c *RuntimeCoordinator) ingestObservation(ctx context.Context, project, run string, epoch int64, j rt.BridgeJournal) error {
	observation, e := j.Observation()
	if e != nil {
		return e
	}
	normalized, e := Decode(Bytes(observation))
	if e != nil {
		return e
	}
	return c.service.observeRuntime(ctx, project, run, epoch, normalized, true)
}

// Recovery imports only already durable facts. Missing or partial facts retain
// UNKNOWN, even for PREPARED records. No path here calls StartBridge.
func (c *RuntimeCoordinator) Recover(ctx context.Context) error {
	rows, e := c.service.DB.QueryContext(ctx, "SELECT d.project,d.run,d.epoch,d.dispatch_key,d.manifest_hash,d.journal_locator FROM runtime_dispatches d WHERE NOT EXISTS (SELECT 1 FROM runtime_prepared_abandonments a WHERE a.project=d.project AND a.run=d.run AND a.epoch=d.epoch)")
	if e != nil {
		return e
	}
	type fact struct {
		project, run, key, hash, locator string
		epoch                            int64
	}
	facts := []fact{}
	for rows.Next() {
		var f fact
		if e = rows.Scan(&f.project, &f.run, &f.epoch, &f.key, &f.hash, &f.locator); e != nil {
			rows.Close()
			return e
		}
		facts = append(facts, f)
	}
	e = rows.Err()
	rows.Close()
	if e != nil {
		return e
	}
	for _, f := range facts {
		handled, err := c.recoverHarness(ctx, f.project, f.run, f.epoch)
		if err != nil {
			return err
		}
		if handled {
			continue
		}
		if f.locator == "" || f.locator != f.key || !filepath.IsLocal(f.locator) {
			if e = c.markUnknown(ctx, f.project, f.run, f.epoch, "no acknowledged worker journal"); e != nil {
				return e
			}
			continue
		}
		directory := filepath.Join(c.config.DataRoot, "runtime-dispatches", f.locator)
		j, terminalError := rt.ReconcileBridge(directory, f.hash)
		if e = c.recoverEffects(ctx, f.project, f.run, directory, f.epoch); e != nil {
			return e
		}
		if e = c.recoverCheckpoints(ctx, f.project, f.run, directory, f.epoch); e != nil {
			return e
		}
		e = terminalError
		if e != nil {
			if e = c.markUnknown(ctx, f.project, f.run, f.epoch, "incomplete terminal facts; reconciliation required"); e != nil {
				return e
			}
			continue
		}
		if e = c.recoverTerminal(ctx, f.project, f.run, f.epoch, directory, j); e != nil {
			return e
		}
	}
	return nil
}
