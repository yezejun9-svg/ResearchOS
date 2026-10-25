//go:build !windows

package qualificationmaintenancejournal

import (
	"errors"
	"os"
	"path/filepath"
)

var errNativeRequired = errors.New("NATIVE_WINDOWS_MAINTENANCE_JOURNAL_REQUIRED")

func CheckOrdinary(root string) error {
	for _, namespace := range []string{QualificationNamespace, ReplacementNamespace} {
		if _, err := os.Lstat(filepath.Join(root, "host", namespace)); err == nil {
			return errNativeRequired
		} else if !os.IsNotExist(err) {
			return err
		}
	}
	return nil
}

func OpenOwnInspection(string, string, string, string) (InspectionPermit, HistoryStatus, error) {
	return InspectionPermit{}, HistoryStatus{}, errNativeRequired
}

func OpenOwnReplacementInspection(string, string, string, []byte) (InspectionPermit, HistoryStatus, error) {
	return InspectionPermit{}, HistoryStatus{}, errNativeRequired
}

func (InspectionPermit) Check(string) (HistoryStatus, error) {
	return HistoryStatus{}, errNativeRequired
}
