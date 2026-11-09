"""Reorder the W04-02 change phase so the applied change is reachable.

Ordering matters here and the reason is a real domain rule, not a test preference: an open
non-decision conflict blocks EVERY later change proposal and acceptance in the project, so the
acceptance and apply leg has to run before the conflict pair is created. The conflict assertions
move to the end, where they also gain the resolution leg that was impossible before.
"""
import io

P = "tests/context/check/w0402.go"
s = io.open(P, encoding="utf-8", newline="").read()

start = s.index("\t// two drafts over the same field")
end = s.index("\t// a task with no frozen context cannot be handed work")
conflict_block = s[start:end]

tail_marker = "\tskip(\"CHG-OPTIONAL-RETRIEVAL-DEGRADES\""
tail_at = s.index(tail_marker)
head = s[:start]
middle = s[end:tail_at]          # second task, gate, unrelated control, apply leg
rest = s[tail_at:]               # the skips and the rest of the file

# the conflict block loses its own acceptance-attempt assertion: the verifier only exists later, and
# the blocked case belongs with the resolution leg at the end
conflict_core = conflict_block.replace('''	// two drafts over the same field, then a conflict naming both: neither draft may move''',
'''	// two drafts over the same field, then a conflict naming both: neither draft may move, the open
	// conflict blocks acceptance, and resolving it names the change that actually settled it''')
assert "CHG-OPEN-CONFLICT-BLOCKS-ACCEPTANCE" not in conflict_core

RESOLVE = '''	// the clean change that was applied earlier is what settles the conflict, and neither draft is
	// rewritten by that decision
	_, resolveState, _ := h.api(ctx, token, "GET", base+"/state", "", "", nil)
	code, resolved, body := h.api(ctx, token, "POST",
		base+"/conflicts/"+Str2(conflict, "id")+"/resolve", domain.ID(), tagOf(resolveState),
		domain.Object{"resolution_proposal_id": Str2(proposalC, "id"),
			"reason": "the independently accepted change settled the field"})
	ok("CHG-CONFLICT-RESOLVED-BY-APPLIED-CHANGE", code == 200 &&
		Str2(resolved, "status") == "RESOLVED" && Str2(resolved, "resolution_proposal_id") == Str2(proposalC, "id"),
		code, Str2(resolved, "status"), body[:min(len(body), 200)])
	_, aFinal, _ := h.api(ctx, token, "GET", base+"/change-proposals/"+Str2(proposalA, "id"), "", "", nil)
	_, bFinal, _ := h.api(ctx, token, "GET", base+"/change-proposals/"+Str2(proposalB, "id"), "", "", nil)
	ok("CHG-RESOLUTION-KEPTS-BOTH-DRAFTS",
		string(domain.Bytes(aFinal)) == beforeA && string(domain.Bytes(bFinal)) == beforeB,
		Str2(proposalA, "id"), Str2(proposalB, "id"))
'''

# the blocked-acceptance case moves into the conflict block, where the conflict is open for real
BLOCKED = '''	// while that conflict stays open, the conflicted draft cannot be independently accepted
	code, _, body = h.api(ctx, verifierToken, "POST", base+"/acceptances", domain.ID(),
		tagOf(proposalA), acceptBody(proposalA, frozen))
	ok("CHG-OPEN-CONFLICT-BLOCKS-ACCEPTANCE", code == 409 && strings.Contains(body, "conflict"),
		code, body[:min(len(body), 200)])
'''

new_conflict = conflict_core + BLOCKED + RESOLVE
s = head + middle + new_conflict + rest
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("phase reordered")
