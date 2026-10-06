"""W05-01 round-5 remediation, applied as guarded exact-fragment patches.

Every anchor must occur exactly once or nothing is written. The round-4 review's four blocking issues are all
of one family: a clause that describes the tree in a way the tree refutes, plus one property disclosed as
blocked whose decisive half was always inside this card's own write scope. So the main change is a real
assertion, and the rest is text that has to say what the code now does.
"""
import io, os

REPO = r"D:/作品集/ResearchOS/research-os"
os.chdir(REPO)
NL = chr(10)
GO = os.path.join("tests", "runtime", "check", "w0501.go")
MUT = os.path.join("execution", "v2.4", "receipts", "W05", "W05-01", "mut_w0501.py")
GEN = os.path.join("execution", "v2.4", "receipts", "W05", "W05-01", "generate_receipt_w0501.py")

CORR = '''	// the Run-identity half of the card's events-and-cost property, asserted rather than disclosed: the
	// worker is started under the claimed domain Run id, task id and lease epoch, the settled journal must
	// carry exactly those values, and the ledger reservation must be keyed to the same Run id. The half
	// that stays disclosed is the dispatch-side event ledger: nothing in this tree launches the adapter
	// from the service, and that is the qualification gate rather than a call this program could have made
	if domain.Str(run, "id") != "" {
		rv, rws, rve := workspace(root, "runbound")
		if rve != nil {
			ok("W0501-RUN-IDENTITY-BOUND-WORKER-JOURNAL", false, rve)
		} else if wErr := os.WriteFile(filepath.Join(rws, "input.txt"), []byte("w0501 run bound 913\\n"), 0o600); wErr != nil {
			ok("W0501-RUN-IDENTITY-BOUND-WORKER-JOURNAL", false, wErr)
		} else {
			epoch := 1
			if f, isNum := runField(run, "lease_epoch").(float64); isNum && int(f) >= 1 {
				epoch = int(f)
			}
			comspec := os.Getenv("COMSPEC")
			rw, rwe := rt.Start(rv, rt.Spec{RunID: domain.Str(run, "id"), TaskID: domain.Str(taskA, "id"),
				Epoch: epoch,
				Commands: []rt.Command{{Executable: comspec,
					Args:      []string{"/c", "copy", "/y", "input.txt", "output.txt"},
					Directory: rws}},
				Environment: rt.Environment(""), Lease: 90 * time.Second, Timeout: 60 * time.Second,
				Outputs: []string{"output.txt"}})
			if rwe != nil {
				ok("W0501-RUN-IDENTITY-BOUND-WORKER-JOURNAL", false, rwe)
			} else {
				rctx, rcancel := context.WithTimeout(ctx, 120*time.Second)
				defer rcancel()
				rj, rjer := rw.Wait(rctx)
				runs, runsErr := h.svc.BudgetUsage(rctx, h.token, h.project, domain.Str(run, "id"))
				key, keyed, other := "fixture-dispatch/" + domain.Str(run, "id"), 0, 0
				for _, v := range domain.Arr(runs, "reserved") {
					hold, isObj := v.(domain.Object)
					if !isObj {
						if m2, isMap := v.(map[string]any); isMap {
							hold = domain.Object(m2)
						} else {
							continue
						}
					}
					if domain.Str(hold, "provider_request_id") == key {
						keyed++
					} else {
						other++
					}
				}
				ok("W0501-RUN-IDENTITY-BOUND-WORKER-JOURNAL",
					rjer == nil && runsErr == nil && rj.State == "SETTLED" &&
						rj.Spec.RunID == domain.Str(run, "id") && rj.Spec.TaskID == domain.Str(taskA, "id") &&
						rj.Spec.Epoch == epoch && len(rj.Artifacts) == 1 &&
						len(rj.Streams) >= 1 && rj.Streams[0].OutHash != "" && keyed >= 1 && other == 0,
					domain.Object{"journal_run": rj.Spec.RunID, "journal_task": rj.Spec.TaskID,
						"journal_epoch": rj.Spec.Epoch, "run_epoch": epoch, "state": rj.State,
						"artifacts": len(rj.Artifacts), "streams": len(rj.Streams),
						"ledger_keyed": keyed, "ledger_other": other,
						"wait_error": fmt.Sprint(rjer), "usage_error": fmt.Sprint(runsErr)})
			}
		}
	}

'''

src = io.open(GO, encoding="utf-8").read()

# 1. insert the correlation block just before the live gate, where run and taskA are still in scope
LIVE = '''	liveGate := exec.Command("python", "-X", "utf8", "ops/ci/runtime.py", "--mode", "live")'''
if src.count(LIVE) != 1:
    raise SystemExit("liveGate anchor count %d" % src.count(LIVE))
src = src.replace(LIVE, CORR + LIVE)

PAIRS = [
 # 2. the mechanism the round-4 reviewer corrected: the old filter did run TestW05Protocol, it excluded
 #    only the sibling reconnect table
 ('''The receipt's captured go test row used to select only TestW05Protocol, which excluded that file; the filter is now widened and the names it actually selects are captured from go test -list rather than typed here, so this class is evidence-backed by a passing accepted test rather than asserted from a fixture nobody ran''',
  '''The filter this receipt captured in round 3 did run TestW05Protocol from that same file, but its anchors excluded the sibling TestW05ProtocolTransientReconnect where the three shapes live; the selection is now widened to both names and the package listing is captured as its own receipt command row, so a reviewer can compare the filter against the names the package really contains instead of taking a family name on faith'''),
 # 3. the CLI row: measured in round 4, so the wording has to match the registry and the dispatch result
 ('''"the deliverable's own-CLI leg is NOT_RUN: no selector in execution/v2.4/commands.json resolves this card to a CLI-level check, apps/cli is inside the card's write scope but is not exercised by any assertion here, and the CLI is separately blocked on the plan-level gap that cli.* commands remain UNBOUND with no owning card"''',
  '''"the deliverable's own-CLI leg is NOT_RUN for a reason measured in the registry rather than assumed: cli.entry_run is the only cli.* key in execution/v2.4/commands.json at revision 14, its selectors are wildcards so the card's own selector triple does match it, its owner_card names the already-accepted W03-01 interactive CLI, and its state is UNBOUND, so dispatching it for this card returns NOT_IMPLEMENTED with zero assertions. A zero-assertion run is never a PASS, so apps/cli stays unexercised here even though it is inside this card's write scope; the plan-level gap that leaves cli.* UNBOUND is owned by the registry, not by this card"'''),
 # 4. the run-correlation row shrinks to the half that is genuinely blocked
 ('''"the card's events-and-cost-bound-to-the-Run property is unmet in this working tree and is disclosed rather than asserted: the adapter phase drives rt.Start under a journal-local run id while the service phase claims a domain Run and reserves its fixture charge, and nothing launches the worker under that Run id and lease epoch, so no evidence links a process tree, its artifacts, its exit code and its stream hashes to a domain Run. Closing it needs the dispatch-to-adapter wiring this card has not built; it is carried as an open obligation, and the fixture dispatch zero charge asserted here is a property of the service ledger, not of that correlation"''',
  '''"only the dispatch-side half of the card's events-and-cost-bound-to-the-Run property stays NOT_RUN, and it is stated as the narrow thing it is: the Run identity join is asserted by W0501-RUN-IDENTITY-BOUND-WORKER-JOURNAL, which starts the worker under the claimed Run id, task id and lease epoch and requires the settled journal and the fixture reservation to carry that same Run id, so what is left is the service launching the adapter on its own, and that is the runtime qualification gate (ops/runtime/capabilities.json and the absent pinned executor build) rather than a call this program could have made"'''),
 # 5. the worker-identity row has to own the registry entries naming this card
 ('''"step 2's worker identity is a cmd.exe process killed and drained through a Windows Job Object, and the SDK model and tool loop the card names is NOT wired: the string SDK appears nowhere in the increment, the adapter phase runs a fixed command line with no model and no tool round trips, and a real model-driven loop needs the provider binding above. The row says plainly what would make it true - a worker whose turns come from an agent SDK loop with the adapter as its tool executor - rather than letting the Job Object stand in for that property"''',
  '''"step 2's worker identity is a cmd.exe process killed and drained through a Windows Job Object, and the SDK model and tool loop the card names is NOT wired: the string SDK appears nowhere in the increment outside this row's own text, and the adapter phase runs a fixed command line with no model and no tool round trips. This card is named as the owner of the two commands that would carry that loop: execution/v2.4/commands.json revision 14 lists fork.worker_launch_rpc and fork.worker_stop with owner_card 'W05-01 worker adapter' and both are state UNBOUND, which makes this card the only owner besides test.runtime of an UNBOUND entry in the v2.4 file. Measured along the chain: third_party/mu and third_party/mu/packages/coding-agent exist, dist/rpc-entry.js does not, and the two commands that would build it, fork.build_worker and fork.install_deps, are themselves UNBOUND under W02-99/W01-G03 rerun. So the half this card owes is the adapter-side launch and stop contract, which the adapter phase does drive and the matrix does kill, and the half it cannot reach is a worker binary that another card's commands must produce. A real model-driven loop additionally needs the provider binding the rows above place with W02-03 and W08-01"'''),
 # 6. row count in the fifth-class row must be the count a reader can reproduce now
 ('''"the card's fifth step 4 class, an explicit or declared protocol error, is covered by accepted code but not by this check program, and the distinction matters: none of the 29 rows here drives turn.failed''',
  '''"the card's fifth step 4 class, an explicit or declared protocol error, is covered by accepted code but not by this check program, and the distinction matters: none of the rows emitted here drives turn.failed'''),
]
for old, new in PAIRS:
    c = src.count(old)
    if c != 1:
        raise SystemExit("go text anchor count %d for %r" % (c, old[:70]))
    src = src.replace(old, new)
io.open(GO, "w", encoding="utf-8", newline=NL).write(src)
print("check program patched")

# 7. matrix: the journal must keep the Spec it was given, and the ledger must keep the Run key
m = io.open(MUT, encoding="utf-8").read()
TAILMARK = ''' {"id": "M20-malformed-line-unclassified", "file": CODEX,
  "marker": \'p.Failure = "invalid_protocol"\',
  "body": \'p.Failure = "" // MUTANT: a malformed line is no longer named\'},
]'''
NEWTAIL = ''' {"id": "M20-malformed-line-unclassified", "file": CODEX,
  "marker": \'p.Failure = "invalid_protocol"\',
  "body": \'p.Failure = "" // MUTANT: a malformed line is no longer named\'},
 {"id": "M21-journal-drops-the-spec-it-was-given", "file": RUNTIME,
  "marker": "w.journal = Journal{Spec: s, Revision: Revision,",
  "body": "w.journal = Journal{Revision: Revision, // MUTANT: the journal no longer records the Run it was started for"},
 {"id": "M22-fixture-reservation-unkeyed", "file": SCOPES,
  "marker": \'"provider_request_id": "fixture-dispatch/" + Str(run, "id")\',
  "body": \'"provider_request_id": "fixture-dispatch", "run_id": nil, "money": Object{"amount": "0", "currency": currency},\'},
]'''
if m.count(TAILMARK) != 1:
    raise SystemExit("matrix tail anchor count %d" % m.count(TAILMARK))

# The matrix replaces WHOLE lines, so the two new bodies are derived from the lines as they really read in
# the tree rather than typed from memory: a hand-copied production line that drifts by one token becomes a
# crash, and a crash is not a kill.
RUNTIME_FILE = os.path.join("adapters", "runtime", "runtime_windows.go")
SCOPES_FILE = os.path.join("internal", "domain", "budget_scopes.go")


def derive(path, needle, transform, label):
    lines = io.open(path, encoding="utf-8").read().split(NL)
    hits = [l for l in lines if needle in l]
    if len(hits) != 1:
        raise SystemExit("derivation needle %s hits %d lines in %s" % (needle, len(hits), path))
    body = transform(hits[0].strip())
    print("derived %s from line: %s" % (label, hits[0].strip()[:80]))
    return body


journal_line = derive(RUNTIME_FILE, "w.journal = Journal{Spec: s,",
                      lambda l: l.replace("Journal{Spec: s,", "Journal{"),
                      "M21")
reserve_line = derive(SCOPES_FILE, '"provider_request_id": "fixture-dispatch/" + Str(run, "id")',
                      lambda l: l.replace('"provider_request_id": "fixture-dispatch/" + Str(run, "id")',
                                          '"provider_request_id": "fixture-dispatch"').replace('"run_id": run["id"]', '"run_id": nil'),
                      "M22")
if "Spec: s," in journal_line or "fixture-dispatch/\"" in reserve_line or '"run_id": run["id"]' in reserve_line:
    raise SystemExit("derived mutant bodies still carry the keyed values; refusing")

BODIES = '''{{"id": "M21-journal-drops-the-spec-it-was-given", "file": RUNTIME,
  "marker": "w.journal = Journal{{Spec: s,",
  "body": "{M21} // MUTANT: the journal no longer records the Run it was started for"}},
 {{"id": "M22-fixture-reservation-unkeyed", "file": SCOPES,
  "marker": \'"provider_request_id": "fixture-dispatch/" + Str(run, "id")\',
  "body": "{M22} // MUTANT: the fixture reservation is no longer keyed to a Run"}}'''
newtail = BODIES.format(M21=journal_line, M22=reserve_line)
io.open(MUT, "w", encoding="utf-8", newline=NL).write(m.replace(TAILMARK, newtail))
print("matrix patched (M21, M22)")


# 8. the receipt must carry the package listing as its own captured command row
g = io.open(GEN, encoding="utf-8").read()
OLD = '''  command_log("go_test_runtime_fixture"), command_log("go_vet_domain")],'''
NEW = '''  command_log("go_test_runtime_fixture"), command_log("go_test_runtime_list"),
  command_log("go_vet_domain")],'''
if g.count(OLD) != 1:
    raise SystemExit("generator commands anchor count %d" % g.count(OLD))
io.open(GEN, "w", encoding="utf-8", newline=NL).write(g.replace(OLD, NEW))
print("generator patched")
