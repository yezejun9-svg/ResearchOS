// Package installation contains pure decisions for a future Windows transaction adapter.
// It does not inspect or change the machine.
package installation

type Route string

const (
	RouteFresh Route = "FRESH_REQUIRES_TRANSACTION"
	RouteExact Route = "EXACT_REINSTALL_REQUIRES_MAINTENANCE"
	RouteUpgrade Route = "UPGRADE_REQUIRES_MAINTENANCE"
	RouteRefuse Route = "REFUSED"
)

type PayloadIdentity struct {
	ManifestSHA256 string
	SourceCommit   string
	Protocol       string
	Schema         int
}

type InstallFacts struct {
	Incoming PayloadIdentity
	Installed *PayloadIdentity
	ProgramExists bool
	RetainedData bool
	OwnedProgram bool
	CanonicalRoots bool
	UnfinishedJournal bool
	HistoricalVerifierRegistration bool
	SupportedSchema bool
	SupportedProtocol bool
}

type Decision struct {
	Route Route
	Reason string
}

// SelectPlan treats every fact as observed input supplied by a future adapter.
// A display version is intentionally absent: it is not payload identity.
func SelectPlan(f InstallFacts) Decision {
	if !f.CanonicalRoots || f.Incoming.ManifestSHA256 == "" || f.Incoming.SourceCommit == "" || f.Incoming.Protocol == "" || f.Incoming.Schema <= 0 {
		return Decision{RouteRefuse, "INVALID_OR_UNKNOWN_ROOT_OR_PAYLOAD"}
	}
	if f.UnfinishedJournal {
		return Decision{RouteRefuse, "UNFINISHED_JOURNAL_NEEDS_RECOVERY"}
	}
	if f.HistoricalVerifierRegistration {
		return Decision{RouteRefuse, "VERIFIER_HISTORY_REQUIRES_SEPARATE_MIGRATION"}
	}
	if !f.SupportedSchema || !f.SupportedProtocol {
		return Decision{RouteRefuse, "UNSUPPORTED_SCHEMA_OR_PROTOCOL"}
	}
	if f.Installed == nil {
		if f.ProgramExists {
			return Decision{RouteRefuse, "UNOWNED_OR_UNVERIFIED_PROGRAM"}
		}
		if f.RetainedData {
			return Decision{RouteUpgrade, "RETAINED_DATA_REQUIRES_COMPATIBILITY_AND_MAINTENANCE"}
		}
		return Decision{RouteFresh, "CLEAN_ROOT_REQUIRES_TRANSACTION"}
	}
	if !f.ProgramExists || !f.OwnedProgram || f.Installed.ManifestSHA256 == "" {
		return Decision{RouteRefuse, "INSTALLED_OWNERSHIP_NOT_VERIFIED"}
	}
	if *f.Installed == f.Incoming {
		return Decision{RouteExact, "SAME_COMPLETE_PAYLOAD_AND_PROVENANCE"}
	}
	return Decision{RouteUpgrade, "CHANGED_PAYLOAD_OR_PROVENANCE"}
}
