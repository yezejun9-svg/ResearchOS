//go:build windows

package domain

import (
	"context"
	"path/filepath"
	"sort"
)

// Dynamic entries are immutable once published. Their credentials stay in the
// host process; they are never saved in an Artifact or a command response.
type preparedRuntimeRoute struct {
	route     RuntimeCoordinatorRoute
	providers []RuntimeProviderRoute
}

func (c *RuntimeCoordinator) runtimeRoutes() []RuntimeCoordinatorRoute {
	c.routeMu.RLock()
	defer c.routeMu.RUnlock()
	out := append([]RuntimeCoordinatorRoute(nil), c.config.Routes...)
	keys := make([]string, 0, len(c.preparedRoutes))
	for key := range c.preparedRoutes {
		keys = append(keys, key)
	}
	sort.Strings(keys)
	for _, key := range keys {
		if c.setupFailures[key] == "" {
			out = append(out, c.preparedRoutes[key].route)
		}
	}
	return out
}

func (c *RuntimeCoordinator) runtimeProviders() []RuntimeProviderRoute {
	c.routeMu.RLock()
	defer c.routeMu.RUnlock()
	out := append([]RuntimeProviderRoute(nil), c.config.Providers...)
	keys := make([]string, 0, len(c.preparedRoutes))
	for key := range c.preparedRoutes {
		keys = append(keys, key)
	}
	sort.Strings(keys)
	for _, key := range keys {
		out = append(out, c.preparedRoutes[key].providers...)
	}
	return out
}

func (c *RuntimeCoordinator) schedulerCredential(project string) string {
	c.routeMu.RLock()
	defer c.routeMu.RUnlock()
	if token := c.schedulerCredentials[project]; token != "" {
		return token
	}
	return c.config.SchedulerToken
}

func runtimeSetupKey(project, model string) string { return project + "/" + model }

// SetRuntimeSetupFailure only records a safe explanation for this model branch.
// It never changes runtime status or any pending effect/UNKNOWN ledger row.
func (c *RuntimeCoordinator) SetRuntimeSetupFailure(project, model, message string) {
	c.routeMu.Lock()
	defer c.routeMu.Unlock()
	if c.setupFailures == nil {
		c.setupFailures = map[string]string{}
	}
	c.setupFailures[runtimeSetupKey(project, model)] = message
}

func (c *RuntimeCoordinator) runtimeSetupFailure(project, model string) string {
	c.routeMu.RLock()
	defer c.routeMu.RUnlock()
	return c.setupFailures[runtimeSetupKey(project, model)]
}

// InstallPreparedRuntime is a trusted host composition method, not an HTTP
// operation. It publishes a route only after rechecking its persisted profile,
// current grants and exact configured model. Qualification is checked later by
// the unchanged admission path; REGISTERED is deliberately allowed here.
func (c *RuntimeCoordinator) InstallPreparedRuntime(ctx context.Context, prepared RuntimeSetupResult, executor, executorToken, schedulerToken string, assets RuntimeSetupAssets) error {
	tx, err := c.service.DB.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	if _, err = resourcePrincipal(tx, schedulerToken, prepared.ProjectID, "SCHEDULER"); err != nil {
		return err
	}
	p, err := authenticate(tx, executorToken)
	if err != nil || p.ID != executor || !p.HasRole("EXECUTOR") || !p.Allowed(prepared.ProjectID, "", "", false) {
		return Fail(403, "FORBIDDEN", "current project runtime executor required")
	}
	runtime, err := load(tx, prepared.ProjectID, "RuntimeRegistration", prepared.RuntimeID)
	if err != nil {
		return err
	}
	_, artifact, err := c.service.currentRuntimeBinding(tx, prepared.ProjectID, runtime)
	if err != nil {
		return err
	}
	profile, err := runtimeProfileBody(tx, prepared.ProjectID, artifact)
	if err != nil {
		return err
	}
	config, ok := profile["model_config"].(map[string]any)
	if !ok || config["ref"] != prepared.ModelRef || profile["build_hash"] != assets.BuildHash || profile["bundle_hash"] != assets.BundleHash || !filepath.IsAbs(assets.Executable) || !filepath.IsAbs(assets.BundleFile) {
		return Fail(412, "STALE_INPUT", "prepared runtime assets or model changed")
	}
	if err = validateRuntimeDispatchProfile(profile); err != nil {
		return err
	}
	if runtime["status"] == "REVOKED" || runtime["status"] == "UNAVAILABLE" {
		return Fail(503, "MODEL_UNAVAILABLE", "prepared runtime is unavailable")
	}
	if runtime["credential_ref"] != nil || profile["credential_revision"] != "none" || !clientConfigurationLoopbackModelEndpoint(Str(config, "endpoint")) {
		return Fail(403, "FORBIDDEN", "automatic preparation supports only credential-free local models")
	}
	providers := make([]RuntimeProviderRoute, 0, 2)
	for _, purpose := range []string{"runtime_qualification", "mu_turn"} {
		providers = append(providers, RuntimeProviderRoute{ID: Str(config, "route"), ProjectID: prepared.ProjectID, RuntimeID: prepared.RuntimeID, Purpose: purpose, Capability: "MODEL", CredentialRevision: "none", Endpoint: Str(config, "endpoint"), MeasurementMode: "LIVE", ModelConfig: config})
	}
	if profile["coding_authorization"] != nil {
		if err = validateLocalQualificationProfile(profile); err != nil {
			return err
		}
		// Host-only TOOL effects have no endpoint, bearer or credential reference.
		// Their existing deterministic zero bound is distinct from MODEL UNKNOWN.
		providers = append(providers, RuntimeProviderRoute{ID: Str(config, "route"), ProjectID: prepared.ProjectID, RuntimeID: prepared.RuntimeID, Purpose: "mu_turn", Capability: "TOOL", CredentialRevision: "local-tools-v1", UpperBound: Object{"amount": "0", "currency": "USD"}, MeasurementMode: "LIVE"})
	}
	route := RuntimeCoordinatorRoute{ProjectID: prepared.ProjectID, RuntimeID: prepared.RuntimeID, ExecutorID: executor, ExecutorToken: executorToken, CommandID: Str(profile, "command_id"), Executable: assets.Executable, BundleFile: assets.BundleFile}
	// Check the exact stored configuration against the proposed immutable snapshot.
	check := &RuntimeCoordinator{service: c.service, config: RuntimeCoordinatorConfig{ClientSchema: c.config.ClientSchema, ConfigurationAuthority: c.config.ConfigurationAuthority, Providers: providers}}
	if err = check.matchStoredClientConfiguration(tx, prepared.ProjectID, prepared.ModelRef, runtime, profile); err != nil {
		return err
	}
	key := runtimeSetupKey(prepared.ProjectID, prepared.ModelRef)
	c.routeMu.Lock()
	defer c.routeMu.Unlock()
	for _, old := range c.config.Routes {
		if old.ProjectID == route.ProjectID && old.RuntimeID == route.RuntimeID {
			return Fail(409, "MODEL_UNAVAILABLE", "runtime already has a static host route")
		}
	}
	if c.preparedRoutes == nil {
		c.preparedRoutes = map[string]preparedRuntimeRoute{}
	}
	if old, found := c.preparedRoutes[key]; found && (old.route.RuntimeID != route.RuntimeID || old.route.ExecutorID != route.ExecutorID || old.route.CommandID != route.CommandID || old.route.Executable != route.Executable || old.route.BundleFile != route.BundleFile) {
		return Fail(412, "STALE_INPUT", "runtime route identity changed; explicit requalification required")
	}
	c.preparedRoutes[key] = preparedRuntimeRoute{route: route, providers: providers}
	if c.schedulerCredentials == nil {
		c.schedulerCredentials = map[string]string{}
	}
	c.schedulerCredentials[prepared.ProjectID] = schedulerToken
	delete(c.setupFailures, key)
	return nil
}
