package runtime

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"strconv"
)

const (
	CodexNativePolicyRevision = "researchos-codex-mxc-readonly-v1"
	CodexNativeSandboxID      = "codex-mxc-permissions-workspace-read-v2"
	CodexNativeCommandID      = "codex-mxc-readonly-v2"
	CodexWindowsSandbox       = "mxc"
	CodexPermissionProfile    = "researchos-readonly"
	CodexExecTransport        = "exec-ephemeral-v1"
	CodexRPCTransport         = "app-server-stdio-first-local-turn-v1"
	CodexRPCPolicyRevision    = "researchos-codex-mxc-rpc-readonly-v1"
	CodexRPCSandboxID         = "codex-mxc-rpc-permissions-workspace-read-v3"
	CodexRPCCommandID         = "codex-mxc-rpc-readonly-v3"
	CodexRPCHelperContract    = "native-0166-windows-fresh-arg0-read-v1"
)

type CodexPolicyIdentity struct {
	Revision, WindowsSandbox, PermissionProfile, RequestedConfigSHA256, BinarySHA256, Transport, HelperContract string
}

type CodexReadiness struct {
	State, Reason  string
	PolicyIdentity CodexPolicyIdentity
}

type CodexReadinessProvider interface{ Snapshot() CodexReadiness }
type CodexReadinessFunc func() CodexReadiness

func (f CodexReadinessFunc) Snapshot() CodexReadiness { return f() }

// This builder is the one source for both the launch argv and its template hash.
// The hash uses placeholders for Host-selected cwd/source, not a caller JSON claim.
func codexRequestedArguments(cwd, source string) []string {
	q := strconv.Quote
	return []string{"exec", "--json", "--ephemeral", "--ignore-user-config", "--skip-git-repo-check", "-C", cwd,
		"-c", `default_permissions="researchos-readonly"`,
		"-c", `windows.sandbox="mxc"`,
		"-c", `permissions.researchos-readonly.filesystem={":root"="deny",":minimal"="read",":workspace_roots"={"."="read"}}`,
		"-c", "permissions.researchos-readonly.workspace_roots={" + q(source) + "=true}",
		"-c", "permissions.researchos-readonly.network.enabled=false",
		"-c", `project_root_markers=[".researchos-codex-root"]`, "-c", `approval_policy="never"`,
		"-c", "features.hooks=false", "-c", "features.plugins=false", "-c", "features.remote_plugin=false",
		"-c", "features.skill_mcp_dependency_install=false", "-c", "features.apps=false",
		"-c", "notify=[]", "-c", `web_search="disabled"`, "-"}
}

func CodexRequestedPolicyIdentity(binarySHA256 string) CodexPolicyIdentity {
	raw, _ := json.Marshal(codexRequestedArguments("<host-cwd>", "<source-workspace>"))
	sum := sha256.Sum256(raw)
	return CodexPolicyIdentity{CodexNativePolicyRevision, CodexWindowsSandbox, CodexPermissionProfile,
		"sha256:" + hex.EncodeToString(sum[:]), binarySHA256, CodexExecTransport, ""}
}

func codexTransport(d CodexDescriptor) string {
	if d.NativeTransport == "" {
		return CodexExecTransport
	}
	return d.NativeTransport
}

func expectedPermissionProfile(transport string) string {
	if transport == CodexRPCTransport {
		return "researchos-readonly-${PROFILE_NONCE}"
	}
	return CodexPermissionProfile
}

// CodexExpectedPolicyIdentity selects only the constructor-sealed transport.
func CodexExpectedPolicyIdentity(d CodexDescriptor) CodexPolicyIdentity {
	if d.NativeTransport == CodexRPCTransport {
		return CodexRPCPolicyIdentity(d.ExecutableHash)
	}
	return CodexRequestedPolicyIdentity(d.ExecutableHash)
}

func CodexAllowsPreparation(r CodexReadiness) bool {
	return r.State == "PREPARATION_READY" || r.State == "READY"
}

// Every caller uses this predicate. A READY snapshot is useful only when its
// full policy identity exactly matches the Host's current requested template.
func EvaluateCodexReadiness(d CodexDescriptor, snapshot CodexReadiness, expected CodexPolicyIdentity) CodexReadiness {
	blocked := func(reason string) CodexReadiness {
		return CodexReadiness{State: "UNAVAILABLE", Reason: reason, PolicyIdentity: expected}
	}
	if !d.Present {
		return blocked("NOT_INSTALLED")
	}
	if !d.ConfigurationControlled {
		return blocked("CONFIG_INHERITANCE_UNVERIFIED")
	}
	if d.AuthState != "LOGGED_IN" {
		return blocked("AUTH_METADATA_REQUIRED")
	}
	if d.UnavailableReason != "" {
		return blocked(d.UnavailableReason)
	}
	if expected.BinarySHA256 == "" || expected.BinarySHA256 != d.ExecutableHash ||
		((codexTransport(d) == CodexRPCTransport && expected.Revision != CodexRPCPolicyRevision) || (codexTransport(d) != CodexRPCTransport && expected.Revision != CodexNativePolicyRevision)) || expected.Transport != codexTransport(d) || expected.WindowsSandbox != CodexWindowsSandbox ||
		expected.PermissionProfile != expectedPermissionProfile(codexTransport(d)) || expected.RequestedConfigSHA256 == "" ||
		snapshot.PolicyIdentity != expected {
		return blocked("CODEX_POLICY_IDENTITY_MISMATCH")
	}
	if snapshot.Reason != "" {
		return blocked(snapshot.Reason)
	}
	if d.NativeTransport == CodexRPCTransport && snapshot.State == "PREPARATION_READY" {
		return CodexReadiness{State: "PREPARATION_READY", PolicyIdentity: expected}
	}
	if snapshot.State != "READY" {
		return blocked("PERMISSION_PROFILE_UNVERIFIED")
	}
	return CodexReadiness{State: "READY", PolicyIdentity: expected}
}
