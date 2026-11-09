package installation

import "strings"

type OwnedItem struct { Identity, SHA256 string }

// RemoveOwned keeps unknown and modified files. A future adapter must verify
// paths and hashes immediately before applying the returned removal list.
func RemoveOwned(current, recorded map[string]OwnedItem) (remove []string, retain []string) {
	for path, actual := range current {
		wanted, known := recorded[path]
		if known && wanted.Identity != "" && wanted.SHA256 != "" && actual == wanted { remove = append(remove, path) } else { retain = append(retain, path) }
	}
	return remove, retain
}

// RestoreOwnedValue uses compare-and-restore; a concurrent or user edit wins.
func RestoreOwnedValue(current, ownedAfter, previous string) (string, bool) {
	if current != ownedAfter { return current, false }
	return previous, true
}

// RemoveOwnedPATH removes exactly one recorded addition only while the entire
// observed PATH still equals the value produced by that addition.
func RemoveOwnedPATH(current, recordedAfter, recordedBefore, ownedEntry string) (string, bool) {
	if current != recordedAfter || ownedEntry == "" { return current, false }
	before := strings.Split(recordedBefore, ";")
	for _, part := range before { if strings.EqualFold(part, ownedEntry) { return current, false } }
	after := strings.Split(recordedAfter, ";")
	count := 0
	for _, part := range after { if part == ownedEntry { count++ } }
	if count != 1 { return current, false }
	expected := recordedBefore
	if expected != "" { expected += ";" }
	expected += ownedEntry
	if expected != recordedAfter { return current, false }
	return recordedBefore, true
}
