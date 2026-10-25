//go:build windows

package host

import "researchos.local/research-os/internal/qualificationmaintenancejournal"

// QualificationMaintenanceRootGate is a pure read. Its caller must already
// hold the native root through a lease or an inherited recovery token.
func QualificationMaintenanceRootGate(root string) error {
	if err := qualificationmaintenancejournal.CheckOrdinary(root); err != nil {
		return err
	}
	return replacementCheckHistoryCurrent(root)
}
