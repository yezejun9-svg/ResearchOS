package installation

import "testing"

func TestOwnershipPreservesUnknownAndChanged(t *testing.T) {
	current := map[string]OwnedItem{"owned": {"install", "a"}, "changed": {"install", "new"}, "unknown": {"other", "x"}}
	recorded := map[string]OwnedItem{"owned": {"install", "a"}, "changed": {"install", "old"}}
	remove, retain := RemoveOwned(current, recorded)
	if len(remove) != 1 || remove[0] != "owned" || len(retain) != 2 { t.Fatalf("%v %v", remove, retain) }
	if got, ok := RestoreOwnedValue("user edit", "owned", "old"); ok || got != "user edit" { t.Fatal(got, ok) }
	if got, ok := RestoreOwnedValue("owned", "owned", "old"); !ok || got != "old" { t.Fatal(got, ok) }
}

func TestPATHOnlyExactOwnedAddition(t *testing.T) {
	if got, ok := RemoveOwnedPATH("A;B;ResearchOS", "A;B;ResearchOS", "A;B", "ResearchOS"); !ok || got != "A;B" { t.Fatal(got, ok) }
	for _, item := range []struct{ current, after, before, entry string }{
		{"A;B;ResearchOS;user", "A;B;ResearchOS", "A;B", "ResearchOS"},
		{"A;B;ResearchOS", "A;B;ResearchOS", "A;B;ResearchOS", "ResearchOS"},
		{"A;B;ResearchOS;ResearchOS", "A;B;ResearchOS;ResearchOS", "A;B", "ResearchOS"},
	} { if _, ok := RemoveOwnedPATH(item.current,item.after,item.before,item.entry); ok { t.Fatal(item) } }
}
