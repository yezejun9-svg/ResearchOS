"""W04-01 round-5 reproduction matrix: every distinct mutation, re-run at the current HEAD.

Rounds 1-4 each produced their own mutation file against the code state of that round, and the
round-4 runner script no longer exists on disk, so a reviewer could not re-run the matrix it was
handed. This script fixes that: it loads the mutation definitions straight out of the round 1-3
runner sources (single source of truth, no transcription), re-states the round-4 U-series and the
routing case against the code as it is now, and adds two mutations aimed at the two assertions the
round-4 review named as coverage gaps.

Each case is applied alone, the construction check is run, the failing assertion ids are recorded,
and the file is restored and hash-verified before the next case. Anything whose anchor is no longer
present is reported as ANCHOR_MISSING rather than being dropped or quietly reworded.
"""
import hashlib
import io
import json
import os
import subprocess

REPO = os.getcwd()
GO = os.path.join(REPO, ".local", "tools", "go1.27.1", "go", "bin", "go.exe")
ENV = dict(os.environ)
ENV.update({"GOTOOLCHAIN": "local", "GOFLAGS": "", "GOENV": "off",
            "GOPATH": os.path.join(REPO, ".local", "gopath"),
            "GOCACHE": os.path.join(REPO, ".local", "gocache"), "RESEARCHOS_GO": GO})

WS = "internal/domain/project_workspace.go"
BS = "internal/domain/project_bootstrap.go"
IV = "adapters/local_workspace/inventory.go"
LG = "tests/context/check/legacy.go"
OUT = os.path.join(".local", os.environ.get("MUT_OUT") or "mutation_selfcheck_w0401_round5.json")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def read(p):
    return io.open(p, encoding="utf-8", newline="").read()


def write(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def run_check():
    r = subprocess.run([GO, "run", "./tests/context/check"], cwd=REPO, env=ENV,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    lines = [l for l in (r.stdout or "").strip().splitlines() if l.startswith("{")]
    if not lines:
        return {"status": "NOJSON", "assertions": 0,
                "failures": [{"id": "RAW", "detail": ((r.stdout or "") + (r.stderr or ""))[:200]}]}
    return json.loads(lines[-1])


def load_defs(script):
    """Take the definitions out of an existing runner without executing its run loop."""
    src = read(script).split("\nreport = [")[0]
    ns = {"__name__": "defs"}
    exec(compile(src, script, "exec"), ns)
    return ns["MUTS"], ns.get("helper", "")


# (round, mutation name, file, anchor, replacement)
matrix = []
for script, tag in ((os.path.join(".local", "mut_w0401.py"), "round1"),
                    (os.path.join(".local", "mut_w0401_round2.py"), "round2"),
                    (os.path.join(".local", "mut_w0401_round3.py"), "round3")):
    muts, _helper = load_defs(script)
    # Round 2 carries a fifth note column; only the first four fields matter here.
    matrix += [(tag, row[0], row[1], row[2], row[3]) for row in muts]

# The round-4 U-series: re-stated against the current source. The originals survived only as
# results, so each anchor below was located by reading the file it targets, not from memory.
UNREACH = '\t\t\tadd(domain.LocalInventoryEntry{Capability: "unreachable_path", LocationRef: relSlash,\n\t\t\t\tStatus: "NOT_ACCESSIBLE", Notes: reasonOf(err)})'
matrix += [
    ("round4", "U1-putOpaque-revision-CAS-removed", WS,
     "\t\tif rev != oldRev+1 {", "\t\tif false {"),
    ("round4", "U2-looksLikePath-forward-slash-branch-removed", WS,
     'return strings.ContainsRune(s, filepath.Separator) || strings.Contains(s, "/") ||',
     "return strings.ContainsRune(s, filepath.Separator) ||"),
    ("round4", "U3-escapesRoot-always-false", IV,
     "\ttgt, err := filepath.EvalSymlinks(path)", "\tif true {\n\t\treturn false\n\t}\n\ttgt, err := filepath.EvalSymlinks(path)"),
    ("round4", "U4-ADS-guard-removed", WS,
     'if stream := strings.Index(strings.TrimPrefix(p, filepath.VolumeName(p)), ":"); stream >= 0 {',
     'if stream := strings.Index(strings.TrimPrefix(p, filepath.VolumeName(p)), ":"); stream >= 0 && false {'),
    ("round4", "U5-unreachable-entry-not-recorded", IV, UNREACH, "\t\t\t_ = relSlash"),
    ("round4", "U6-replay-row-not-persisted", BS,
     '\tif e := s.putOpaque(ctx, tx, project, "BootstrapReplay", "replay-"+in.CommandID, record); e != nil {\n\t\treturn nil, e\n\t}',
     "\t_ = record"),
    ("round4", "T6b-routing-card-binding-forwarded-to-legacy", LG,
     '\tif check == "W04-01" {\n\t\treturn false\n\t}',
     '\tif check == "W04-01" {\n\t\treturn true\n\t}'),
    # New in round 5: teeth for the two assertions the round-4 review named as coverage gaps.
    ("round5", "V1-per-file-failure-list-not-persisted", BS,
     "Failures: failuresList(failures),", "Failures: Empty(),"),
    ("round5", "V2-measurement-mode-hardcoded-to-LIVE", BS,
     '"measurement_mode": mode, "content_hash": upload["content_hash"]',
     '"measurement_mode": "LIVE", "content_hash": upload["content_hash"]'),
]

# The round-2 R-series and two round-3 cases target code that the accepted fixes then rewrote, so
# their literal anchors are gone. Rather than dropping the properties, each is re-stated against
# the gate that now carries it. These five are the current-code equivalents.
FOREIGN = 'if b.PrincipalID != p.ID {\n\t\treturn nil, Fail(403, "FORBIDDEN", "workspace was authorised for a different principal")'
matrix += [
    ("round5", "W1-register-ownership-gate-removed", WS,
     FOREIGN, "if false {\n\t\treturn nil, Fail(403, \"FORBIDDEN\", \"unused\")"),
    ("round5", "W2-revoke-ownership-gate-removed", WS,
     'if b.PrincipalID != p.ID {\n\t\treturn Fail(403, "FORBIDDEN", "only the principal that authorised this workspace may revoke it")',
     "if false {\n\t\treturn Fail(403, \"FORBIDDEN\", \"unused\")"),
    ("round5", "W3-bootstrap-ownership-gate-removed", BS,
     FOREIGN, "if false {\n\t\treturn nil, Fail(403, \"FORBIDDEN\", \"unused\")"),
    ("round5", "W4-listing-filter-removed", WS,
     "\t\tif b.PrincipalID == p.ID {\n\t\t\tout = append(out, b)",
     "\t\tif true {\n\t\t\tout = append(out, b)"),
    ("round5", "W5-revoked-root-not-typed", WS,
     'case strings.Contains(err.Error(), "pinned workspace root is unavailable"),',
     'case strings.Contains(err.Error(), "__never_matches__"),'),
    # T2 and T3 were carried from round 3 unchanged and now break compilation instead of reaching a
    # named assertion, because the variables their branches reference became single-use. These two
    # variants disable the branch without orphaning the variable, so the signal is the assertion.
    ("round5", "T2b-directory-shared-across-principals-allowed", WS,
     "\t} else if taken {", "\t} else if taken && false {"),
    ("round5", "T3b-replay-not-scoped-to-reference", BS,
     '\t} else if e == nil && owner == p.ID && ref != "" && ref != in.AuthorizedWorkspaceRef {',
     '\t} else if e == nil && owner == p.ID && ref != "" && ref != in.AuthorizedWorkspaceRef && false {'),
    # The two branches the round-4 review reported as surviving because nothing fed them: both are
    # now asserted, so each of these mutations must fail a named id.
    ("round5", "X1-read-path-accepts-a-path-shaped-reference", WS,
     '\tif looksLikePath(ref) {\n\t\treturn nil, Fail(403, "FORBIDDEN", "an authorized workspace reference is not a filesystem path")',
     '\tif false && looksLikePath(ref) {\n\t\treturn nil, Fail(403, "FORBIDDEN", "unused")'),
    ("round5", "X2-expired-selection-case-deleted", WS,
     '\tcase strings.Contains(err.Error(), "SELECTION_EXPIRED"):\n\t\treturn Fail(410, "SELECTION_EXPIRED", "this directory choice expired")\n',
     ""),
    # The round-1 addendum runner is gone from disk too, so its two load-bearing cases are re-stated
    # here. Y16 needs two files at once, which the row format allows by handing path/old/new as lists.
    ("round5", "Y18-scanner-follows-junctions", IV,
     '\t\tif d.Type()&fs.ModeSymlink != 0 || d.Type() == fs.ModeIrregular || reparsePoint(path) ||\n\t\t\t(d.IsDir() && escapesRoot(rootReal, path)) {',
     "\t\tif false {"),
    ("round5", "Y16-both-collision-guards-removed", [WS, BS],
     ['if clash, e := s.bindingCommandOwner(ctx, tx, in.CommandID); e == nil && clash != "" && clash != p.ID {',
      '\tif Str(o, "principal_id") != principal {'],
     ['if clash, e := s.bindingCommandOwner(ctx, tx, in.CommandID); false && clash != "" && clash != p.ID {',
      "\tif false && Str(o, \"principal_id\") != principal {"]),
]

only = [s for s in (os.environ.get("MUT_ONLY") or "").split(",") if s]
seen, cases = set(), []
for row in matrix:
    if row[1] in seen:
        continue
    if only and not any(o in row[1] for o in only):
        continue
    seen.add(row[1])
    cases.append(row)

def edits_of(row):
    """Normalise a case into [(file, anchor, replacement), ...]; most cases are a single edit."""
    _tag, _name, path, old, new = row
    if isinstance(path, list):
        return list(zip(path, old, new))
    return [(path, old, new)]


if os.environ.get("PREFLIGHT"):
    # Cheap check before a multi-minute run: every anchor must be present exactly once in its file.
    bad = []
    for row in cases:
        for path, old, _new in edits_of(row):
            c = read(path).count(old)
            if c != 1:
                bad.append("%-52s %-6s %s anchor count %d" % (row[1], row[0], path, c))
    print("cases=%d" % len(cases))
    print("\n".join(bad) if bad else "all anchors unique")
    # Eight cases are expected to be missing: their anchors were rewritten by the accepted fixes, and
    # the run reports them as ANCHOR_MISSING with the current case that carries the property. Anything
    # beyond that list is a real surprise and has to be looked at in the printed lines.
    print("expected_missing=%d (R1-R6, T6, T12)" % 8)
    raise SystemExit(0)

report = []
pristine = {p: sha(p) for p in (WS, BS, IV, LG)}
helper = load_defs(os.path.join(".local", "mut_w0401.py"))[1]
base_bs = read(BS)
for tag, name, _path, _old, _new in cases:
    if tag == "round1":
        # MG12 swaps ensureStage for a helper that only exists during this phase.
        write(BS, base_bs.replace("\nfunc (s *Service) authorisedBinding(",
                                  helper + "\nfunc (s *Service) authorisedBinding(", 1))
    elif sha(BS) != pristine[BS]:
        write(BS, base_bs)
    site = edits_of((tag, name, _path, _old, _new))
    originals, bad_anchor = {}, None
    for path, old, new in site:
        original = read(path)
        if original.count(old) != 1:
            bad_anchor = original.count(old)
            break
        originals[path] = original
    if bad_anchor is not None:
        report.append({"mutation": name, "round": tag, "file": site[0][0], "status": "ANCHOR_MISSING",
                       "anchor_count": bad_anchor})
        print("%-52s %-6s ANCHOR %d" % (name, tag, bad_anchor), flush=True)
        continue
    hashes = {p: sha(p) for p in originals}
    for path, old, new in site:
        write(path, originals[path].replace(old, new))
    d = run_check()
    failed = [f["id"] for f in (d.get("failures") or [])]
    for path, _old, _new in site:
        write(path, originals[path])
    report.append({"mutation": name, "round": tag,
                   "file": site[0][0] if len(site) == 1 else [p for p, _o, _n in site],
                   "status": d["status"], "assertions": d.get("assertions", 0), "failed_ids": failed,
                   "restored": all(hashes[p] == sha(p) for p in hashes)})
    print("%-52s %-6s %-7s failed=%d %s" % (name, tag, d["status"], len(failed), ",".join(failed[:4])), flush=True)

if sha(BS) != pristine[BS]:
    write(BS, base_bs)
d = run_check()
report.append({"baseline": d["status"], "assertions": d.get("assertions"),
               "failures": d.get("failures") or [],
               "all_files_restored": all(sha(p) == h for p, h in pristine.items())})
print("BASELINE", d["status"], d.get("assertions"), "restored=", all(sha(p) == h for p, h in pristine.items()))
write(OUT, json.dumps(report, indent=1, ensure_ascii=False))
