"""Writes this review's deliverable (qoder-desktop:/root/w1302_verifier_r1).

Kept as a generator rather than a hand-typed JSON so the artefact digests are computed from the bytes on disk at
settle time, and so re-emitting is a no-op if nothing else changed.
"""
import hashlib
import io
import json
import os
import subprocess

RD = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(RD, "..", "..", "..", "..", ".."))


def g(*a):
    return subprocess.run(list(a), capture_output=True, text=True, cwd=ROOT).stdout.strip()


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def rel(p):
    return "execution/v2.4/receipts/W13/W13-02/" + os.path.basename(p)


ck = json.load(open(os.path.join(ROOT, "execution/v2.4/checkpoint.json"), encoding="utf-8"))
row = [x for x in json.load(open(os.path.join(ROOT, "execution/v2.4/step_state.json"), encoding="utf-8"))["steps"]
       if x["id"] == "W13-02"][0]
drift = g("git", "diff", "--stat", "661e2589", "HEAD", "--", "apps/web", "apps/desktop", "tests/ui",
          "execution/v2.4/receipts/W13/W13-02")

R = {
 "reviewer_id": "qoder-desktop:/root/w1302_verifier_r1",
 "builder_id": "qoder-desktop:/root/construction",
 "step_id": "W13-02",
 "step_title": "打通对话、工具、文件Diff与双端接续",
 "parent_task": "W13",
 "verdict": "ACCEPT_WITH_LIMITATIONS",
 "checked_at": "2026-10-04T12:38:00Z",
 "repository_head_at_review": g("git", "rev-parse", "HEAD"),
 "card_parked_at_head": "661e2589ee0f4c0206e8cafa75557cfaf5651bb9",
 "receipt_head_at_report": "c53a9cfdea951e0f9c0aa3b4f2d270001b15e8e4",
 "checkpoint_revision_at_review": ck["revision"],
 "checkpoint_revision_at_assignment": 135,
 "head_drift_during_review": {
   "observed_heads_in_order": ["661e2589", "9c0e964e", "a958700e", "53fdb2d7", g("git", "rev-parse", "HEAD")],
   "cause": "other cards committing under this review (W05-03 round-3 registration, W07-01 test.sources.live binding)",
   "did_this_cards_inputs_move": drift or "no drift: this card's product files, check program and receipt directory are byte-identical at the settle-time head",
   "consequence": "every measurement here describes the parked card tree, verified against the pinned blobs"},
 "identity_isolation": {
   "step_state_read": "read-only; this reviewer wrote no byte to step_state.json or checkpoint.json",
   "status": row["status"],
   "executor_id": row.get("executor_id"),
   "verifier_id_key_present_on_the_row": "verifier_id" in row,
   "row_evidence_list": row.get("evidence"),
   "receipt_json_verifier_id": json.load(open(os.path.join(RD, "receipt.json"), encoding="utf-8")).get("verifier_id"),
   "receipt_independent_review_status": "NOT_RUN",
   "registration_face_still_shows_execution_reported_without_a_verifier": row["status"] == "EXECUTION_REPORTED" and "verifier_id" not in row,
   "reviewer_never_signed_as_builder": True},
 "acceptance_scope": {
   "accepts": "the W13-02 card increment only: the test.ui.recovery binding for check_id W13-02, the two JavaScript protocol surfaces, the renderer continuity screen, and this card's own check program and evidence set",
   "does_not_accept": ["parent W13", "W13-99", "C23", "C24", "C25", "A04", "C26 (the case this card's command forwards to)"],
   "note": "no formal case among C23/C24/C25/A04 is signed here; card acceptance is not parent, gate or case acceptance"},
 "methods": [
   "re-hashed all 16 registered evidence files and compared each to `git show 661e2589:<path>`: 16/16 byte-identical (reviewer_evidence_digests.json)",
   "re-ran the card's verification command through the dispatcher three times (2977d055, d1c068da, 0dce0b2e) and ran the same program three more times on a clean tree with watched-file hashes before and after each run (reviewer_repeat_runs.json)",
   "exercised both selector guards: --check-id with --case-id, and no selector at all - both answer COMMAND_FAILED with 0 assertions and a named W1302-SELECTORS-REQUIRED id (invocations bbd399aa, 7a83e8d5)",
   "verified every cited invocation on disk: 69e15282 NOT_IMPLEMENTED exit 3 with an empty id list; 393cf98b and 8dad9335 PASS 28 exit 0; 4d99b687 INVALID_ASSERTION_REPORT exit 9 with 26 ids; a2d57af9 COMMAND_FAILED exit 1 with 27 ids; 33a3ffac and 1f92fcfc PASS 31",
   "re-ran the pinned-node two-surface comparison with a probe of the reviewer's own (reviewer_surfaces_probe.js). Node verified by hash first: sha256 5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6 equals locked.json, version v24.9.0; no PATH node was used anywhere",
   "re-ran the builder's own driver once with the pinned node for cross-checking (reviewer_driver_rerun_pinned_node.json) and wrote a second, independent comparison rather than trusting it",
   "ruled every renderer-accepted envelope against the shipped core: internal/domain/client_protocol.go DecodeEnvelope called from a reviewer-written Go program run with the pinned toolchain .local/tools/go1.27.1/go/bin/go.exe (reviewer_envelope_authority.go -> reviewer_envelope_authority_round1.json)",
   "ran the forwarded C26 path end to end and read both the harness report and its child browser report (reviewer_c26_forward_run.json), plus the 5 earlier runs of the same phase on disk",
   "wrote and ran 12 reviewer mutants across apps/web/src/v2client.js, apps/web/src/continuity.jsx, apps/desktop/main/lib/v2.js and tests/ui/continuity/producer_probe.py; each run restored byte-exactly with a sha comparison and was followed by a clean recheck (reviewer_mut_matrix_round1.json, reviewer_mut_matrix_round2.json)",
   "registry: compared execution/v2.4/commands.json at 95c2b1ab^ against 95c2b1ab field by field, re-parsed it at the settle-time head, and printed every key's selectors to look for a reroute",
   "scope: git show --stat over all six W13-02 commits plus the three evidence commits"],
 "findings": {
   "claim_1_binding": {
     "claim": "test.ui.recovery is BOUND to tests/ui/continuity/check/main.py for check_id W13-02, forwarding C26 to ops/ci/ui.py --phase recovery; before binding it answered NOT_IMPLEMENTED / exit 3 / 0 assertions (69e15282) and two post-binding rounds reported PASS 28 (393cf98b, 8dad9335)",
     "verdict": "CONFIRMED, subject to problems[0] on stability",
     "measurement": "registry entry state=BOUND, selectors {task_id:[W13],check_id:[W13-02],case_id:[C26]}, argv ['-X','utf8','tests/ui/continuity/check/main.py'], owner_card W13-02; 69e15282 on disk is NOT_IMPLEMENTED with exit 3 and zero assertion ids; my identical-input runs PASS 28, PASS 28, COMMAND_FAILED 27; both builder rounds reproduce when the box is not contended"},
   "claim_2_two_surfaces_agree": {
     "claim": "v2.js and v2client.js agree on 23 methods equal to the schema's x-method-contracts including each payload's required set, on 69 legal envelopes, 11 refusal reasons and 9 reply classifications",
     "verdict": "CONFIRMED as an agreement property; the three nouns overstate their counts",
     "measurement": "reviewer probe: 69 comparison cases, 69 byte-identical, zero mismatch rows; both CONTRACT tables equal the schema's 23 published methods on name, payload def, result def and required set (0 diff rows) and also equal the Go core's methodsV2 (23) and writeMethods (9), so the property is stronger than claimed - three surfaces, not two; classify agrees on 20/20 reply shapes the reviewer designed (the card probes 9). Counted honestly: of the 69 cases 47 are accepted envelopes and 22 are local refusals (writer_epoch 11, project_id 9, MODEL_CHANGE_WITHOUT_EPOCH 2); the 11 refusal cases produce 10 distinct reason strings; the 9 classification cases produce 8 distinct kinds. The evidence file itself uses the accurate words legal_probes/refusal_cases/classify_cases - only the receipt prose does not"},
   "claim_3_real_browser_producer_coverage": {
     "claim": "each of the 23 methods has a data-producer control that, clicked in Chromium against the built bundle with a recording stub host, sends exactly its own method to /v2/command: 24 commands, 23 distinct, no off-protocol request, and an unmet precondition sends nothing",
     "verdict": "CONFIRMED at method granularity, with two measured limits",
     "measurement": "browser_producer_probe_run.json reproduces inside my own green runs: traffic {commands 24, distinct_methods 23, paths ['/v2/command'], off_protocol [], all_authorized true, missing_clicks []}, 23 clicked rows each sending only its own method, unmet_precondition {present true, disabled true, commands_after 0}. LIMIT A: the click loop takes the first enabled control per method, so of the three session.control buttons only PAUSE ever sends; the first-render DOM held 22 controls under 19 distinct tags. LIMIT B: what is recorded is a method name plus an envelope, never a payload the core would accept - see claim_3_core_authority"},
   "claim_3_core_authority": {
     "claim": "(receipt limits_observed) the stub host does not enforce client_protocol.go, so the probe proves wiring and envelope presence, not core acceptance",
     "verdict": "DISCLOSED BY THE BUILDER AND NOW MEASURED: the divergence runs renderer-permissive / core-strict",
     "measurement": "72 envelopes the renderer accepts were fed to domain.DecodeEnvelope: 53 accepted, 8 refused. The 8 come from 4 payloads the delivered screen really sends - provider.models {refresh:true, allow_network:false} -> CATALOG_REFRESH_WITHOUT_CONSENT; provider.probe {allow_network:false, max_output_tokens:64} -> PROBE_WITHOUT_NETWORK_CONSENT (max_output_tokens>32 would also trip UNBOUNDED_PROBE); workspace.write with task_id '' -> MISSING_FIELD:task_id; workspace.write with expected_content_hash null -> OVERWRITE_NULL_HASH - plus two driver-fixture payloads (permission.respond action_digest 'sha256:abc' -> MISSING_FROZEN_SCOPE_DIGEST). Rule by rule, v2client.js mirrors DecodeEnvelope exactly on protocol_version, command_id, client_id, method-known, empty-string project/session references, the attach claim/read epoch pair, the write-class project+revision+epoch triple and MODEL_CHANGE_WITHOUT_EPOCH; it does not mirror validatePayload (path escape, hash shape, probe bounds, decision vocabulary), and it is stricter than the core in two inert places (EmptyPayload extra keys and the schema required list, which the core's decode gate does not enforce: all three reviewer-built veto cases are CORE_ACCEPTS). Direction: nothing the renderer sends today is silently swallowed, but four of the 23 producers are wired to commands the real core rejects and no row on this card says so"},
   "claim_4_mutation_matrix": {
     "claim": "mutation_selfcheck_round1.json caught 4 with 2 anchor-missing and round1b re-took those 2, both caught",
     "verdict": "CONFIRMED as recorded; the recorded matrix is NOT reproducible from the frozen driver",
     "measurement": "buckets match the delivered bytes: anchors A, B, E and F occur exactly once in the files, while round-1's C and D anchors occur 0 times, so the two anchor-missing rows are honest gaps rather than concealed survivors, and round1b's corrected anchors occur once. But both drivers abort from their frozen location: their ROOT is dirname(__file__)+'..' which resolves to execution/v2.4/receipts/W13, so running mut_w1302_round1.py raises FileNotFoundError on <receipts/W13>/apps/web/src/v2client.js before writing anything (reproduced; worktree unchanged). A reviewer must rewrite the driver to re-measure, which I did"},
   "claim_5_accepted_neighbours_unharmed": {
     "claim": "test.ui.routes --check-id W13-01 PASS 31 (33a3ffac, 1f92fcfc)",
     "verdict": "CONFIRMED",
     "measurement": "both invocations exist on disk with PASS, 31 assertion ids, exit 0, key test.ui.routes, selectors {W13, W13-01, ''}; my own re-run at head a958700e gave PASS 31 (aa8e695d); node over apps/desktop/main/lib/ipc.js reports the accepted eleven flat channels still 11 with the 23 v2 methods namespaced separately"},
   "not_verified_honesty": {
     "claim": "the not_verified rows are disclosures, not excuses",
     "verdict": "HONEST on the live-chain and crash-replay rows; honest-but-unmeasured-when-cheap on the C26 row; correct by plan rule on the cases row",
     "measurement": "row 1 (CLI creates a session, Desktop joins/pauses/hands off, CLI resumes) needs desktop.shell_launch and cli.entry_run, both state UNBOUND in the registry now (argv ['apps/desktop'], wildcard selectors, owner_card 'W13-01 renderer integration'); rebinding another card's key is not this card's scope in substance, and no call inside tests/ui/**, apps/web or apps/desktop closes it. Row 2 (crash/restart without side-effect replay): the client half is asserted and my R11 mutant shows the meaningful part IS discriminated - rewriting resync() to re-send instead of re-read turns the browser row red; the browser-lifecycle half belongs to ops/ci/ui.py (outside scope) and to the shared frozen harness tests/ui/browser_smoke.py. Row 3 (C26 never run through this key): I ran it - bound and reachable, returns FAIL at 9 of 11 expected checks with the child aborting at browser_smoke.py:190 on a 15000ms wait, and 5 earlier runs of that phase, all predating this card, also FAIL; so the statement was true, but the measurement cost about three minutes on hardware the builder already had and would have told the next reader the gate is red"},
   "scope_discipline": {
     "claim": "only DESKTOP/** (apps/desktop), UI/** (apps/web), tests/ui/** and the receipt directory, plus the shared registry append",
     "verdict": "CONFIRMED with one convention note",
     "measurement": "b007e0b9 and ba617cf0 apps/desktop/main/lib/v2.js; 06b2cd84 apps/desktop/main/lib/ipc.js, main/main.js, preload/preload.js; 7883e368 apps/web/src/{v2client.js, continuity.jsx, main.jsx, screens.jsx}; 95c2b1ab apps/web/src/continuity.jsx + execution/v2.4/commands.json + tests/ui/continuity/{check/main.py, producer_probe.py, surfaces_driver.js}; 22fc6e38 and 661e2589 only execution/v2.4/receipts/W13/W13-02/**; eb3ebf1d only execution/v2.4/{checkpoint.json, step_state.json}. No apps/cli, internal/, ops/ or spec/ path appears in any W13-02 commit and no accepted card's file shows whitespace or formatting churn. Convention note: the park commit writes two files outside the declared write_scope, which is how every reported card in this repo parks (W05-03 971166ff, W06-02, W05-02) - recorded, not charged"},
   "registry_integrity": {
     "claim": "commands.json still parses and the append rerouted no pre-existing selector",
     "verdict": "CONFIRMED",
     "measurement": "95c2b1ab^ -> 95c2b1ab: 19 -> 20 keys, added exactly ['test.ui.recovery'], removed [], key order equals old order plus the appended key, and all 19 pre-existing entries deep-compare identical including selectors. At the settle-time head the file parses with 21 keys (test.sources.live was appended later by W07-01) and the printed selector table shows no wildcard swallowing a W13 row. The applied writer (bind_selector_writer.py) refuses a hash-registered commands.json, refuses an existing key, aborts unless a no-op re-dump reproduces the current bytes, and asserts both no-other-entry-changed and append-only order; I re-derived those four conditions against the file as it stands"},
   "evidence_registration": {
     "claim": "(brief) recompute the digests listed in the receipt's commits/artifact section",
     "verdict": "NOTHING WAS PINNED; all seven cited commits resolve",
     "measurement": "receipt.json carries no file digests and the step_state row lists evidence: [], so the 16 files were unpinned before this review. I hashed all 16 and compared each to the blob at the parked head: 16/16 identical (reviewer_evidence_digests.json). The cited commits 7883e368, 95c2b1ab, 22fc6e38, eb3ebf1d, 661e2589, c53a9cfd (head_at_report) and 23a29fd5 all resolve to commits with the stated subjects"}
 },
 "own_mutants": {
   "total": 12,
   "targets": {"apps/web/src/v2client.js": 5, "apps/web/src/continuity.jsx": 4, "apps/desktop/main/lib/v2.js": 1, "tests/ui/continuity/producer_probe.py": 2},
   "counts": {"caught_by_card_id": 7, "caught_by_gate_id_only": 4, "survived": 1, "anchor_missing": 0, "crashed_ill_formed": 0},
   "restored_byte_exact": {"round1": True, "round2": True},
   "per_mutant": [
     {"id": "R1-renderer-drops-action-digest-from-required", "file": "apps/web/src/v2client.js", "class": "caught_by_card_id", "killed_by": ["W1302-RENDERER-TABLE-MATCHES-THE-FROZEN-SCHEMA", "W1302-ENVELOPES-AGREE-ACROSS-SURFACES"], "other_rows_moved": []},
     {"id": "R2-renderer-sends-without-a-credential", "file": "apps/web/src/v2client.js", "class": "caught_by_card_id", "killed_by": ["W1302-REFUSAL-REASONS-AGREE"], "other_rows_moved": ["W1302-BROWSER-PRODUCERS-DISPATCH-THEIR-COMMAND", "W1302-PROBE-FIXTURES-MATCH-THE-PUBLISHED-SCHEMA", "W1302-PRODUCERS-ALL-REACH-ONE-ENDPOINT", "W1302-SCREEN-RENDERS-A-CONTROL-PER-PRODUCER", "W1302-UNMET-PRECONDITION-SENDS-NOTHING"]},
     {"id": "R3-renderer-adopts-session-id-from-a-result-body", "file": "apps/web/src/v2client.js", "class": "caught_by_card_id", "killed_by": ["W1302-SESSION-ID-ADOPTED-ONLY-FROM-THE-ENVELOPE"], "other_rows_moved": []},
     {"id": "R4-screen-send-becomes-restyle-only", "file": "apps/web/src/continuity.jsx", "class": "caught_by_card_id", "killed_by": ["W1302-BROWSER-PRODUCERS-DISPATCH-THEIR-COMMAND"], "other_rows_moved": ["W1302-SESSION-ID-ADOPTED-ONLY-FROM-THE-ENVELOPE"], "note": "the card's own negative 按钮只变样式 built at the screen layer: the button still clears the transcript and no command leaves"},
     {"id": "R5-screen-save-drops-the-base-hash", "file": "apps/web/src/continuity.jsx", "class": "caught_by_gate_id_only", "killed_by": [], "other_rows_moved": ["W1302-SESSION-ID-ADOPTED-ONLY-FROM-THE-ENVELOPE"], "reason": "冲突静默覆盖 at the payload layer: no expected row moved. The browser row records method names, never payload values, and the stub host answers anything. The row that did move is a driver row this mutant cannot reach. Against the real core the same payload is refused as OVERWRITE_NULL_HASH (measured), so this is a gate-coverage gap, not a live silent-overwrite path"},
     {"id": "R6-stub-host-status-result-loses-a-required-key", "file": "tests/ui/continuity/producer_probe.py", "class": "caught_by_gate_id_only", "killed_by": [], "other_rows_moved": ["W1302-SESSION-ID-ADOPTED-ONLY-FROM-THE-ENVELOPE"], "reason": "W1302-PROBE-FIXTURES-MATCH-THE-PUBLISHED-SCHEMA did not move: producer_probe.py:129-133 skips the required-key check for exactly those methods whose published result has required keys and are not in a 6-name exempt list"},
     {"id": "R7-stub-session-events-result-loses-a-required-key", "file": "tests/ui/continuity/producer_probe.py", "class": "caught_by_card_id", "killed_by": ["W1302-PROBE-FIXTURES-MATCH-THE-PUBLISHED-SCHEMA"], "other_rows_moved": ["W1302-SESSION-ID-ADOPTED-ONLY-FROM-THE-ENVELOPE"], "reason": "positive control paired with R6: the same edit to a fixture the guard does reach moves the row, so R6's non-movement is the guard's reach and not the mutant's fault"},
     {"id": "R8-shell-drops-the-claimed-epoch-rule", "file": "apps/desktop/main/lib/v2.js", "class": "caught_by_card_id", "killed_by": ["W1302-REFUSAL-REASONS-AGREE"], "other_rows_moved": ["W1302-PROBE-FIXTURES-MATCH-THE-PUBLISHED-SCHEMA", "W1302-SESSION-ID-ADOPTED-ONLY-FROM-THE-ENVELOPE"], "reason": "the shell half of the mirror is discriminated as well"},
     {"id": "R9-screen-cancels-nothing", "file": "apps/web/src/continuity.jsx", "class": "caught_by_gate_id_only", "killed_by": [], "other_rows_moved": ["W1302-SCREEN-RENDERS-A-CONTROL-PER-PRODUCER"], "reason": "deleting the cancel producer entirely reddens the gate only because the rendered-control count falls from 22 to 21 under that row's total>=22 floor; no row names the cancel control and the click set never exercises it"},
     {"id": "R10-screen-stops-adopting-a-body-session-id", "file": "apps/web/src/continuity.jsx", "class": "survived", "killed_by": [], "outcome": "PASS 28, exit 0", "reason": "continuity.jsx:115 adopts a session id out of the reply's RESULT BODY (`if (value.session_id && !value.snapshot) client.adopt({ sessionId: value.session_id })`), which is the behaviour asserted_properties[4] says never happens. Removing the line changes nothing on this card because W1302-SESSION-ID-ADOPTED-ONLY-FROM-THE-ENVELOPE drives createV2Client.send() directly and never renders the screen. The survivor is reasoned, not argued away: the claim holds for the library and is false for the delivered surface; the id still originates in a host reply rather than a pasted transcript, so it does not open the card's 复制聊天记录假接续, but no assertion covers the screen's adoption path"},
     {"id": "R11-recovery-resend-instead-of-re-read", "file": "apps/web/src/continuity.jsx", "class": "caught_by_card_id", "killed_by": ["W1302-BROWSER-PRODUCERS-DISPATCH-THEIR-COMMAND"], "other_rows_moved": [], "reason": "recovery replays a side effect instead of re-reading events: distinct_methods falls to 22 and the row moves, so the no-replay property is discriminated at the session.events producer"},
     {"id": "R12-renderer-drops-the-expected-revision-guard", "file": "apps/web/src/v2client.js", "class": "caught_by_gate_id_only", "killed_by": [], "other_rows_moved": ["W1302-BROWSER-PRODUCERS-DISPATCH-THEIR-COMMAND"], "reason": "deleting the MISSING_FIELD:expected_revision refusal moves no refusal row - the driver's 11 illegal cases contain no expected_revision case, and the 69-case matrix cannot see it because the writer_epoch refusal fires first in every state that lacks a revision. The gate still went red, but through the browser wiring row, which is an unrelated discriminator"}
   ],
   "unattributed_pattern": "in round 1, 6 of 8 runs listed W1302-SESSION-ID-ADOPTED-ONLY-FROM-THE-ENVELOPE among their failures, including mutants that cannot reach it, and the same driver run standalone passes it (reviewer_driver_rerun_pinned_node.json). Round 2 recorded the hashes of the five files the check reads before and after every run and saw no movement, and round 2 showed none of this pattern; I report it as unattributed rather than explained - the box was under heavy concurrent load during round 1 (3-4 minutes per run there, about 50 seconds per run in round 2)"
 },
 "problems": [
   {"label": "reservation", "id": "P1-verification-command-not-deterministic",
    "statement": "the card's own registered verification command returns exit 1 on unchanged input. Of 8 identical-input clean-tree runs by this reviewer, 5 reported PASS 28 and 3 reported red, with three different symptoms: missing_clicks [session.events, session.control, permission.respond]; Page.goto net::ERR_CONNECTION_RESET against the probe's own 127.0.0.1 stub; only 3 of 24 commands recorded. Including the builder's two rounds the population is 10 runs, 7 green, 3 red",
    "evidence": "invocations 2977d055, d1c068da, 0dce0b2e; reviewer_repeat_runs.json runs 0/1/2; the clean rechecks in reviewer_mut_matrix_round1.json (PASS 28) and reviewer_mut_matrix_round2.json (FAIL 27)",
    "why_not_a_blocker": "every red run fails loudly with a named id and never passes vacuously; the substance of claims 1-5 reproduces whenever it is green; and the fix - the probe's fixed 180/260 ms waits against control-enable races in tests/ui/continuity/producer_probe.py - is inside this card's own write scope",
    "required_before": "the parent W13 gate, case C26, or any later card that re-runs this key as a regression must not be closed on this gate as it stands; the executor should make the browser phase wait on the condition rather than on a timer, or the row should state its own pass ratio"},
   {"label": "reservation", "id": "P2-fixture-schema-guard-covers-7-of-23",
    "statement": "asserted_properties[5] says the probe's stub fixtures are asserted against the published schema so that a re-issued schema trips the probe. Measured: the guard checks 7 of the 23 result bodies and skips 16, and among the skipped ones host.status misses 11 of 12 required keys, provider.probe misses 8 of 8, project.bootstrap misses 5 of 6 - while build_fixtures() still returns problems []",
    "evidence": "tests/ui/continuity/producer_probe.py:129-133; the per-method required/missing table computed during this review; mutants R6 (unchecked fixture, row does not move) and R7 (checked fixture, row moves) in reviewer_mut_matrix_round1.json",
    "required_before": "correct that bullet when the row is registered; the stub's answers are not contract-shaped for three methods, so the browser phase is outbound-wiring evidence only"},
   {"label": "reservation", "id": "P3-envelope_reason_classification_counts",
    "statement": "'69 legal envelopes, 11 refusal reasons, 9 reply classifications' are case counts: 47 accepted plus 22 refused, 10 distinct reason strings, 8 distinct classification kinds. The agreement property itself holds and I extended it",
    "evidence": "reviewer_surfaces_probe_result.json P1/P2/P3; surfaces_agreement_probe.json summary fields legal_probes/refusal_cases/classify_cases"},
   {"label": "reservation", "id": "P4-cancel-control-is-never-exercised",
    "statement": "the click loop takes the first enabled control per method, so session.control is exercised only as PAUSE; CANCEL and RESUME send nothing in any recorded run. Deleting the cancel control is caught only by an arithmetic floor on the rendered-control count, and no row inspects a cancel reply's settled/children_stopped/queue_empty - those three words appear in this card's test layer only inside the stub fixture, which answers children_stopped: 1 and queue_empty: false under status COMPLETED, a shape the real core's DecodeResponse refuses as CANCEL_COMPLETED_UNSETTLED",
    "evidence": "reviewer_mut_matrix_round2.json R9; tests/ui/continuity/producer_probe.py:96-97 and CLICK_ORDER; grep -n 'settled|children_stopped|queue_empty' over tests/ui/continuity; internal/domain/client_protocol.go:531-536",
    "note": "the receipt does state 取消残留worker失败 is NOT ADDRESSED BY THIS CARD, so this is a disclosed non-claim sharpened by measurement, not a hidden one"},
   {"label": "reservation", "id": "P5-body-session-id-adoption_survives",
    "statement": "continuity.jsx:115 adopts a session id from the reply's result body; removing it is a clean PASS 28 survivor, and asserted_properties[4] states the opposite as a property of the product",
    "evidence": "reviewer_mut_matrix_round2.json R10"},
   {"label": "limitation", "id": "P6-frozen-mutation-drivers-do-not-run-from-where-they-are-pinned",
    "statement": "mut_w1302_round1.py and mut_w1302_round1b.py abort from the receipt directory because ROOT resolves to execution/v2.4/receipts/W13; the recorded buckets are nevertheless consistent with the delivered bytes",
    "evidence": "python execution/v2.4/receipts/W13/W13-02/mut_w1302_round1.py -> FileNotFoundError before any write; anchor occurrence counts A/B/E/F = 1, C/D = 0, round1b C/D = 1"},
   {"label": "limitation", "id": "P7-no-evidence-digests-were-pinned",
    "statement": "the receipt registers no sha256 for its 16 evidence files and the step_state row lists evidence: [], so nothing pinned those bytes before this review",
    "evidence": "reviewer_evidence_digests.json: 16/16 equal to the blob at 661e2589"},
   {"label": "limitation", "id": "P8-four_producers_send_commands_the_core_refuses",
    "statement": "provider.models, provider.probe and two reachable workspace.write payloads are refused by the shipped core's DecodeEnvelope while the recording stub answered COMPLETED, so the green browser row cannot see it",
    "evidence": "reviewer_envelope_authority_round1.json counts {agree_accept 53, js_accepts_core_refuses 8, js_refused 11} and the js_veto_cases rows showing the opposite direction exists but is inert"},
   {"label": "limitation", "id": "P9-c26-forwarded-gate-is-red",
    "statement": "the phase this card forwards to returns FAIL at 9 of 11 expected checks and has never passed (6 runs on disk, all FAIL, 5 predating this card). It does not block the card - the card signs no case - but the registry note promises a forwarding the harness cannot yet satisfy",
    "evidence": "reviewer_c26_forward_run.json; execution/receipts/W13/c26-recovery/registered/*/report.json"}
 ],
 "limitations": [
   "this review measured the parked card at 661e2589 while HEAD moved five times beneath it; git diff over apps/web, apps/desktop, tests/ui and this receipt directory between 661e2589 and the settle-time head is empty, so no measurement here is tree-ambiguous",
   "another agent ran Go work in this same worktree throughout: go.mod and tests/runtime/cli_contract/v2verbs.go were dirty while my C26 run and my first mutation pass executed, and cli.exe was untracked. I touched none of it. Round 2 wrapped every run in before/after hashes of the five files the check reads and saw zero movement; round 1 lacked that guard, which is why its 6 anomalous rows are recorded as unattributed instead of explained",
   "no Go suite was run, no real core was started and no provider was called: the core side went through domain.DecodeEnvelope as a library call inside a reviewer-written program, so no cost was incurred and none is claimed",
   "the C26 forward path was run once by me; the other five red runs on disk are other agents' records, so the cause (a timeout inside tests/ui/browser_smoke.py:190) is corroborated across time but my own outcome measurement is a single run",
   "no Electron shell was launched: desktop.shell_launch and cli.entry_run are UNBOUND, so the desktop half of the live chain is unmeasured by anyone, including this review",
   "the two-surface comparisons execute the source modules under the pinned node, not the built bundle, so a bundler-level divergence between the surfaces would not show here; the browser phase does run the bundle, and my screen mutants ran through a fresh vite build",
   "check_program_direct_run.json in the evidence set is an intermediate 27-assertion PASS carrying the pre-split id W1302-METHOD-TABLE-MATCHES-THE-FROZEN-SCHEMA; the receipt narrates two rejected runs but not this one, so one pinned file has no stated place in the story",
   "the W13-02 row's two selector guards answer with the detail text 'no selector means nothing was asked of this program' even when the real cause was two selectors arriving together (invocation bbd399aa): correct refusal, misleading wording"
 ],
 "verdict_scope": {
   "W13-02-OUTPUT": "ACCEPTED with a stated reduction: one host and no second dispatcher is measured (single /v2/command path, 23 distinct producers, zero off-protocol requests, the accepted eleven flat shell channels intact, and no renderer-side scheduler in v2client.js). The '真实CLI/Desktop操作同一任务' half is REFUSED - it needs two UNBOUND bindings and this review did not close it",
   "W13-02-NEGATIVE": "PARTIALLY ACCEPTED: 按钮只变样式 refuted at method granularity and reproduced as a caught mutant (R4); 冲突静默覆盖 refuted at the client re-baseline layer - the card's own W1302-REFUSED-WRITE / IN-PROGRESS / TRANSPORT-LOSS-DOES-NOT-REBASELINE rows, which the builder's round-1b mutant C kills and my R2/R8 also move - though the write payload layer is unwatched (R5) and the expected_revision guard moves no refusal row (R12); 复制聊天记录假接续 REFUSED as a live-session claim (the card does not assert it) and sharpened by survivor R10 at the screen layer; 取消残留worker失败 accepted as the card's own honest non-claim, with P4 showing the cancel control is never exercised",
   "W13-02-EVIDENCE": "ACCEPTED with three corrections to make when the row is registered: asserted_properties[4] and [5] are not true of the delivered screen and of the fixture guard as written; the envelope/reason/classification figures are case counts; the pinned mutation drivers do not run from where they are pinned. Nothing in the evidence set was found to be fabricated - every cited invocation exists on disk with the cited status and id count, and all 16 files match the parked blobs",
   "check_ids_refused": ["C26", "C23", "C24", "C25", "A04", "parent W13 gate", "W13-99"],
   "for_the_registrar": "the row should carry verifier_id qoder-desktop:/root/w1302_verifier_r1, verdict ACCEPT_WITH_LIMITATIONS, the 5 reservations and 8 limitations above, and an evidence list built from the 16 digests in reviewer_evidence_digests.json. This reviewer wrote nothing to step_state.json or checkpoint.json"
 },
 "reproducibility": {
   "card_command": "python execution/command_dispatcher/dispatch.py test.ui.recovery --task-id W13 --check-id W13-02",
   "reviewer_invocations": {"2977d055": "PASS 28", "d1c068da": "PASS 28", "0dce0b2e": "COMMAND_FAILED 27",
                            "aa8e695d": "test.ui.routes W13-01 PASS 31", "d13fa0ec": "C26 forward COMMAND_FAILED",
                            "bbd399aa": "two-selector guard COMMAND_FAILED 0", "7a83e8d5": "no-selector guard COMMAND_FAILED 0"},
   "clean_tree_runs": {"pass_28": 5, "red": 3, "ids": ["2977d055", "d1c068da", "repeat run1", "repeat run2", "round1 clean recheck", "0dce0b2e", "repeat run0", "round2 clean recheck"]},
   "pinned_toolchains": {"node_path": "C:\\nvm4w\\nodejs\\node.exe", "node_sha256_matches_locked_json": True, "node_version": "v24.9.0",
                         "go": ".local/tools/go1.27.1/go/bin/go.exe", "python": "the dispatcher's locked-table python"},
   "reviewer_drivers": ["reviewer_mut_round1.py (supports --dry to assert anchors first)", "reviewer_mut_round2.py", "reviewer_repeat_probe.py 3", "reviewer_surfaces_probe.js <ROOT>", "reviewer_envelope_authority.go"]
 },
 "artefacts_written": []
}

files = [f for f in sorted(os.listdir(RD)) if f.startswith("reviewer_")]
R["artefacts_written"] = [{"path": rel(os.path.join(RD, f)), "sha256": sha(os.path.join(RD, f)),
                           "bytes": os.path.getsize(os.path.join(RD, f))} for f in files]
out = os.path.join(RD, "independent_review_round1.json")
io.open(out, "w", encoding="utf-8", newline="\n").write(json.dumps(R, ensure_ascii=False, indent=1) + "\n")
print("WROTE", out, os.path.getsize(out), sha(out))
print("artefacts", len(R["artefacts_written"]))
