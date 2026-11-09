//go:build windows

package domain

import (
	"context"
	"database/sql"
)

// ResolveGoalBinding selects only when this authenticated client has exactly
// one current project workspace and the host has exactly one current Mu model
// route for that project. Neither a CLI config nor an old session supplies an
// implicit authority for a project-level goal.start.
func (c *RuntimeCoordinator) ResolveGoalBinding(ctx context.Context, tx *sql.Tx, principal, project, client string) (string, string, error) {
	rows, err := tx.QueryContext(ctx, `SELECT body FROM domain_objects WHERE project='' AND kind=?`, KindWorkspaceBinding)
	if err != nil {
		return "", "", err
	}
	var workspace string
	for rows.Next() {
		var raw string
		if err = rows.Scan(&raw); err != nil {
			rows.Close()
			return "", "", err
		}
		b, decodeErr := decodeBinding(raw)
		if decodeErr != nil {
			rows.Close()
			return "", "", decodeErr
		}
		if b.ProjectID == nil || *b.ProjectID != project || b.PrincipalID != principal || b.ClientID != client || b.Status != WorkspaceActive {
			continue
		}
		if workspace != "" {
			rows.Close()
			return "", "", Fail(409, "RESOURCE_BLOCKED", "project goal has multiple authorized workspaces")
		}
		workspace = b.AuthorizedRef
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return "", "", err
	}
	if workspace == "" {
		return "", "", Fail(503, "RESOURCE_BLOCKED", "project goal has no uniquely authorized workspace")
	}

	model := ""
	if c.config.ConfigurationAuthority != nil {
		s := &ClientService{Domain: c.service, Doc: c.config.ClientSchema, ConfigurationAuthority: c.config.ConfigurationAuthority}
		owner, e := s.configurationOwner(ctx, tx, principal)
		if e != nil {
			return "", "", e
		}
		head, e := readClientConfigurationHead(ctx, tx, c.config.ClientSchema, owner, principal)
		if e != nil {
			return "", "", Fail(503, "MODEL_UNAVAILABLE", "current configuration head is invalid")
		}
		if head.Ref != "" {
			if e = c.ValidateBinding(ctx, tx, principal, project, workspace, head.Ref); e != nil {
				return "", "", e
			}
			return workspace, head.Ref, nil
		}
	} else {
		var heads int
		if err = tx.QueryRowContext(ctx, `SELECT count(*) FROM host_model_config_heads WHERE principal=?`, principal).Scan(&heads); err != nil {
			return "", "", err
		}
		if heads > 0 {
			return "", "", Fail(503, "MODEL_UNAVAILABLE", "configuration head requires trusted host authority")
		}
	}
	seen := map[string]bool{}
	for _, route := range c.config.Routes {
		if route.ProjectID != project {
			continue
		}
		runtime, loadErr := load(tx, project, "RuntimeRegistration", route.RuntimeID)
		if loadErr != nil {
			return "", "", loadErr
		}
		_, artifact, bindErr := c.service.currentRuntimeBinding(tx, project, runtime)
		if bindErr != nil {
			continue
		}
		profile, profileErr := runtimeProfileBody(tx, project, artifact)
		if profileErr != nil {
			return "", "", profileErr
		}
		config, _ := profile["model_config"].(map[string]any)
		ref := Str(config, "ref")
		if profile["backend"] != runtimeMuBackend || ref == "" {
			continue
		}
		if route.CommandID != profile["command_id"] {
			return "", "", Fail(403, "FORBIDDEN", "model route command differs from current profile")
		}
		if err = validateRuntimeModelConfig(profile); err != nil {
			return "", "", err
		}
		if seen[ref] {
			return "", "", Fail(409, "RESOURCE_BLOCKED", "project goal model route is ambiguous")
		}
		seen[ref] = true
		if model != "" {
			return "", "", Fail(409, "RESOURCE_BLOCKED", "project goal has multiple model configurations")
		}
		model = ref
	}
	if model == "" {
		return "", "", Fail(503, "MODEL_UNAVAILABLE", "project goal has no current Mu model configuration")
	}
	if err = c.ValidateBinding(ctx, tx, principal, project, workspace, model); err != nil {
		return "", "", err
	}
	return workspace, model, nil
}
