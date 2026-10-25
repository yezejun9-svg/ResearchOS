//go:build !windows

package main

import "errors"

func openReleaseHostSourceLease(string) (any, error) {
	return nil, errors.New("NATIVE_WINDOWS_SOURCE_LEASE_REQUIRED")
}
