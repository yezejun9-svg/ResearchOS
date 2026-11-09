//go:build windows

package host

import (
	"context"
	"encoding/hex"
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"researchos.local/research-os/internal/domain"
)

// RuntimeSetup is the offline product composition, called by the single
// coordinator after recovery and before its scan. It never invokes a provider,
// begins a qualification Run, accepts a Task, or upgrades runtime status.
type RuntimeSetup struct {
	candidate *TrustedCandidatePolicy
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
	var assets domain.RuntimeSetupAssets
	if setup.candidate != nil {
		assets, err = LoadTrustedCandidateRuntimeSetupAssets(*setup.candidate)
	} else {
		assets, err = LoadRuntimeSetupAssets(setup.assetsDir)
	}
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

// TrustedCandidatePolicy is supplied only by the host composition. It is never
// decoded from request payloads or selected via environment variables.
type TrustedCandidatePolicy struct {
	AssetRoot    string
	ManifestHash string
	BundleHash   string
	NodeHash     string
	SourceHash   string
}

// LoadTrustedCandidateRuntimeSetupAssets leaves the installed loader and its
// legacy pin untouched. The caller must pin the independently accepted build.
func LoadTrustedCandidateRuntimeSetupAssets(policy TrustedCandidatePolicy) (domain.RuntimeSetupAssets, error) {
	bad := func() (domain.RuntimeSetupAssets, error) {
		return domain.RuntimeSetupAssets{}, domain.Fail(503, "MODEL_UNAVAILABLE", "trusted candidate runtime assets unavailable")
	}
	if !filepath.IsAbs(policy.AssetRoot) || !candidateHash(policy.BundleHash) || !candidateHash(policy.NodeHash) || !candidateHash(policy.SourceHash) || policy.ManifestHash != "sha256:9e5dd1e5d93f19c6a4aa5eb5c0e2ebd7f0d1e05a987f6ec03963b4b560139da9" {
		return bad()
	}
	root, err := filepath.EvalSymlinks(policy.AssetRoot)
	if err != nil || !strings.EqualFold(filepath.Clean(root), filepath.Clean(policy.AssetRoot)) {
		return bad()
	}
	read := func(name string, limit int64) ([]byte, error) {
		p := filepath.Join(root, name)
		info, e := os.Lstat(p)
		if e != nil || !info.Mode().IsRegular() || info.Size() <= 0 || info.Size() > limit {
			return nil, errors.New("candidate resource invalid")
		}
		actual, e := filepath.EvalSymlinks(p)
		if e != nil || !strings.EqualFold(actual, p) {
			return nil, errors.New("candidate resource reparse")
		}
		return os.ReadFile(p)
	}
	raw, err := read("mu-worker.mjs.build.json", 64<<10)
	if err != nil {
		return bad()
	}
	var meta struct {
		SourceMode string `json:"source_mode"`
		Manifest   string `json:"candidate_manifest_sha256"`
		Base       string `json:"candidate_base"`
		Patch      string `json:"candidate_patch_sha256"`
		Review     string `json:"independent_review_sha256"`
		Protocol   string `json:"protocol_capability"`
		Bundle     string `json:"bundle_sha256"`
		Source     string `json:"source_sha256"`
		Bytes      int64  `json:"bundle_bytes"`
		Inputs     int    `json:"compiled_inputs"`
		Census     string `json:"compiled_inputs_sha256"`
	}
	if json.Unmarshal(raw, &meta) != nil || meta.SourceMode != "ACCEPTED_M0_CANDIDATE" || "sha256:"+meta.Manifest != policy.ManifestHash || meta.Base != "7ec619a16a932ae02daa7c2e6132d266528a1da8" || meta.Patch != "f82f8b8f866ae920bb769b657faf0a1a8709844979422fa409cb5bbc5194ad67" || meta.Review != "13c6ce9fbad76c6e6f2b2c8537bbaa2e662dc5539709c0161fa5219d06dd7489" || meta.Protocol != "RESEARCHOS_PAUSE_V1" || "sha256:"+meta.Bundle != policy.BundleHash || "sha256:"+meta.Source != policy.SourceHash || meta.Inputs < 2 || !candidateHash("sha256:"+meta.Census) {
		return bad()
	}
	bundle, err := read("mu-worker.mjs", 128<<20)
	if err != nil || int64(len(bundle)) != meta.Bytes || domain.Digest(bundle) != policy.BundleHash {
		return bad()
	}
	node, err := read("node.exe", 128<<20)
	if err != nil || len(node) < 2 || string(node[:2]) != "MZ" || domain.Digest(node) != policy.NodeHash {
		return bad()
	}
	return domain.RuntimeSetupAssets{Executable: filepath.Join(root, "node.exe"), BundleFile: filepath.Join(root, "mu-worker.mjs"), BuildHash: policy.NodeHash, BundleHash: policy.BundleHash}, nil
}
func candidateHash(value string) bool {
	if len(value) != 71 || !strings.HasPrefix(value, "sha256:") {
		return false
	}
	_, err := hex.DecodeString(value[7:])
	return err == nil
}

// NewTrustedCandidateRuntimeSetup is an explicit host-only composition point.
func (h *Host) NewTrustedCandidateRuntimeSetup(service *domain.Service, schema *domain.SchemaDoc, policy TrustedCandidatePolicy) (*RuntimeSetup, error) {
	if _, err := LoadTrustedCandidateRuntimeSetupAssets(policy); err != nil {
		return nil, err
	}
	setup := h.NewRuntimeSetup(service, schema, policy.AssetRoot)
	setup.candidate = &policy
	return setup, nil
}
