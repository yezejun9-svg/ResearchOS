//go:build windows

package host

import (
	"context"
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"sync"
	"time"

	"researchos.local/research-os/internal/domain"
)

// RuntimeSetup is the offline product composition, called by the single
// coordinator after recovery and before its scan. It never invokes a provider,
// begins a qualification Run, accepts a Task, or upgrades runtime status.
type RuntimeSetup struct {
	host      *Host
	service   *domain.Service
	schema    *domain.SchemaDoc
	assetsDir string
	mu        sync.Mutex
	cache     map[string]runtimeSetupAttempt
}
type runtimeSetupAttempt struct {
	next    time.Time
	message string
}

func (h *Host) NewRuntimeSetup(service *domain.Service, schema *domain.SchemaDoc, assetsDir string) *RuntimeSetup {
	return &RuntimeSetup{host: h, service: service, schema: schema, assetsDir: assetsDir, cache: map[string]runtimeSetupAttempt{}}
}

// LoadRuntimeSetupAssets consumes the normal Mu build producer's adjacent
// .build.json and a packaged Node executable. No PATH/test environment lookup,
// download, build, executable launch or model call occurs during setup.
func LoadRuntimeSetupAssets(directory string) (domain.RuntimeSetupAssets, error) {
	var assets domain.RuntimeSetupAssets
	bad := func() (domain.RuntimeSetupAssets, error) {
		return assets, domain.Fail(503, "MODEL_UNAVAILABLE", "local runtime assets unavailable: install runtime/node.exe, mu-worker.mjs and its matching .build.json, or set --runtime-assets-dir")
	}
	if directory == "" {
		return bad()
	}
	root, err := filepath.Abs(directory)
	if err != nil {
		return bad()
	}
	root, err = filepath.EvalSymlinks(root)
	if err != nil {
		return bad()
	}
	read := func(name string, limit int64) ([]byte, string, error) {
		path := filepath.Join(root, name)
		info, e := os.Lstat(path)
		if e != nil || !info.Mode().IsRegular() || info.Size() <= 0 || info.Size() > limit {
			return nil, "", errors.New("runtime resource unavailable")
		}
		raw, e := os.ReadFile(path)
		return raw, path, e
	}
	metaRaw, _, err := read("mu-worker.mjs.build.json", 64<<10)
	if err != nil {
		return bad()
	}
	var meta struct {
		BundleHash    string `json:"bundle_sha256"`
		BundleBytes   int64  `json:"bundle_bytes"`
		SourceHash    string `json:"source_sha256"`
		SDKVersion    string `json:"sdk_version"`
		AIVersion     string `json:"ai_version"`
		MuCommit      string `json:"mu_commit"`
		VendoredFiles int    `json:"vendored_files_verified"`
	}
	if json.Unmarshal(metaRaw, &meta) != nil || meta.MuCommit != "8dfebe36508ac0c2508735bb866756dab9283e74" || meta.VendoredFiles != 5083 || len(meta.SourceHash) != 64 || meta.SDKVersion == "" || meta.AIVersion == "" {
		return bad()
	}
	bundle, bundlePath, err := read("mu-worker.mjs", 128<<20)
	if err != nil || int64(len(bundle)) != meta.BundleBytes || domain.Digest(bundle) != "sha256:"+meta.BundleHash {
		return bad()
	}
	node, nodePath, err := read("node.exe", 256<<20)
	if err != nil || len(node) < 2 || string(node[:2]) != "MZ" {
		return bad()
	}
	return domain.RuntimeSetupAssets{Executable: nodePath, BundleFile: bundlePath, BuildHash: domain.Digest(node), BundleHash: domain.Digest(bundle)}, nil
}

func (setup *RuntimeSetup) Reconcile(ctx context.Context, coordinator *domain.RuntimeCoordinator) error {
	setup.mu.Lock()
	defer setup.mu.Unlock()
	h := setup.host
	if h == nil || setup.service == nil || setup.schema == nil {
		return domain.Fail(503, "HOST_UNAVAILABLE", "offline runtime setup host unavailable")
	}
	if _, err := h.reverify(); err != nil {
		return err
	}
	candidates, err := setup.service.RuntimeSetupCandidates(ctx, h.InstanceID())
	if err != nil {
		return err
	}
	var failures []error
	for _, candidate := range candidates {
		key := candidate.ProjectID + "/" + candidate.ModelRef
		prior := setup.cache[key]
		if time.Now().Before(prior.next) {
			continue
		}
		err := setup.prepare(ctx, coordinator, candidate)
		if err == nil {
			// Credentials are short-lived. Reconcile their current roles/grants and
			// lineage before renewing them; never revive a revoked identity.
			setup.cache[key] = runtimeSetupAttempt{next: time.Now().Add(5 * time.Minute)}
			continue
		}
		message := "local runtime preparation is blocked; configuration and history remain available"
		var fault *domain.Fault
		if errors.As(err, &fault) {
			message = fault.Message
		}
		coordinator.SetRuntimeSetupFailure(candidate.ProjectID, candidate.ModelRef, message)
		setup.cache[key] = runtimeSetupAttempt{next: time.Now().Add(10 * time.Second), message: message}
		if prior.message != message {
			failures = append(failures, domain.Fail(503, "MODEL_UNAVAILABLE", message))
		}
	}
	return errors.Join(failures...)
}

func (setup *RuntimeSetup) prepare(ctx context.Context, coordinator *domain.RuntimeCoordinator, candidate domain.RuntimeSetupCandidate) error {
	h := setup.host
	// Current OS and protected host binding, not a caller-supplied principal or
	// environment secret, authorizes the temporary internal credential.
	metadata, err := h.ConfigurationMetadata(ctx, candidate.PrincipalID, "", nil)
	if err != nil || metadata.OwnerHost != h.InstanceID() {
		return domain.Fail(403, "FORBIDDEN", "runtime setup requires the bound local host Owner")
	}
	token, err := setup.service.IssueCredential(ctx, candidate.PrincipalID, time.Minute)
	if err != nil {
		return err
	}
	defer h.revokeCredentialByHash(ctx, candidate.PrincipalID, domain.Digest([]byte(token)))
	if err = setup.service.ValidateRuntimeSetup(ctx, token, candidate, setup.schema, h); err != nil {
		return err
	}
	assets, err := LoadRuntimeSetupAssets(setup.assetsDir)
	if err != nil {
		return err
	}
	prepared, err := setup.service.PrepareClientRuntime(ctx, token, candidate, assets, setup.schema, h)
	if err != nil {
		return err
	}
	ids := map[string]string{}
	tokens := map[string]string{}
	installed := false
	defer func() {
		if !installed {
			for role, value := range tokens {
				_ = h.revokeCredentialByHash(ctx, ids[role], domain.Digest([]byte(value)))
			}
		}
	}()
	for _, role := range []string{"SCHEDULER", "EXECUTOR"} {
		ids[role], err = setup.service.EnsureRuntimeSetupPrincipal(ctx, token, candidate.ProjectID, role)
		if err != nil {
			return err
		}
		tokens[role], err = setup.service.IssueCredential(ctx, ids[role], MaxSessionTTL)
		if err != nil {
			return err
		}
	}
	if err = coordinator.InstallPreparedRuntime(ctx, prepared, ids["EXECUTOR"], tokens["EXECUTOR"], tokens["SCHEDULER"], assets); err != nil {
		return err
	}
	installed = true
	return nil
}
