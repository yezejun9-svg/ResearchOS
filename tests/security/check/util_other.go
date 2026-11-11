//go:build !windows

package main

import "errors"

// foreignAccountPID, makeJunction and removeJunction are Windows-specific: the check reports the
// affected cases as not verified rather than pretending they passed elsewhere.
func foreignAccountPID() (uint32, error) {
	return 0, errors.New("peer account comparison requires Windows")
}
func makeJunction(string, string) (bool, string) {
	return false, "junctions are a Windows filesystem feature"
}
func removeJunction(string) {}

func fileGrantsOnlyCurrentUser(string) string { return "ACL verification requires Windows" }
func dirGrantsOnlyCurrentUser(string) string  { return "ACL verification requires Windows" }
