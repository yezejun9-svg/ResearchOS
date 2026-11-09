import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = Path("D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r2-20261015")
FIVE = [
    "adapters/runtime/qualification_failure_proof_windows.go",
    "adapters/runtime/qualification_failure_proof_windows_test.go",
    "internal/domain/runtime_command_queue_windows_test.go",
    "internal/domain/runtime_qualification_failure_windows.go",
    "internal/domain/runtime_qualification_failure_windows_test.go",
]
NINE = [
    "adapters/runtime/bridge_windows.go",
    "adapters/runtime/qualification_failure_proof_windows.go",
    "adapters/runtime/qualification_failure_proof_windows_test.go",
    "internal/domain/runtime_broker_windows.go",
    "internal/domain/runtime_command_queue_windows.go",
    "internal/domain/runtime_command_queue_windows_test.go",
    "internal/domain/runtime_coordinator_windows.go",
    "internal/domain/runtime_qualification_failure_windows.go",
    "internal/domain/runtime_qualification_failure_windows_test.go",
]


def digest(path: Path) -> dict:
    data = path.read_bytes()
    return {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def save(name: str, value: object) -> None:
    (ROOT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


for source, target in [
    ("r2-132-delta-patch.stdout.raw", "delta-exact-five-from-75e5257c.patch"),
    ("r2-133-whole-patch.stdout.raw", "whole-nine-from-f48fca0e.patch"),
]:
    shutil.copyfile(ROOT / source, ROOT / target)

commands = []
for path in sorted(ROOT.glob("r2-*.result.json")):
    tag = path.name.removesuffix(".result.json")
    result = json.loads(path.read_text(encoding="utf-8"))
    command = ROOT / (tag + ".command.json")
    commands.append({
        "tag": tag,
        "argv": json.loads(command.read_text(encoding="utf-8")).get("argv") if command.exists() else None,
        "cwd": json.loads(command.read_text(encoding="utf-8")).get("cwd") if command.exists() else None,
        "native_exit": result.get("native_exit"),
        "stdout_sha256": result.get("stdout_sha256"),
        "stderr_sha256": result.get("stderr_sha256"),
        "stdout_raw": tag + ".stdout.raw",
        "stderr_raw": tag + ".stderr.raw",
        "result": path.name,
    })
save("command-index.json", {"schema": "researchos.qualification-failure-B-r2-command-index.v1", "count": len(commands), "commands": commands})

failed = [c for c in commands if c["native_exit"] != 0]
save("diagnostic-ledger.json", {
    "schema": "researchos.qualification-failure-B-r2-diagnostic-ledger.v1",
    "meaning": "Append-only captured attempts; nonzero exits are retained and not reset by later passes.",
    "native_nonzero_count": len(failed),
    "native_nonzero": failed,
    "known_initial_failures": {
        "r2-038": "gofmt was not on PATH; corrected to pinned Go tool",
        "r2-041": "exploratory search path did not exist",
        "r2-047": "first recipe JSON was malformed; corrected and rerun",
        "r2-059": "first card lookup used wrong path",
        "r2-060": "card lookup did not find file",
        "r2-063": "first recipe JSON was malformed; corrected and rerun",
        "r2-066": "initial refusal matrix exposed invalid TOOL seed; corrected",
        "r2-068": "initial marker mutant exposed missing guard; corrected",
        "r2-077": "first recipe JSON was malformed; corrected and rerun",
        "r2-088": "first recipe JSON was malformed; corrected and rerun",
        "r2-104": "exploratory exact helper name search returned no match",
        "r2-107": "wrong test filter exited 0 with no tests to run; r2-109 ran the actual test",
        "r2-113": "receipt lookup used wrong filename",
        "r2-115": "Windows GBK console could not encode replacement character; raw-byte read r2-116 succeeded",
        "r2-118": "exploratory multi-path search included absent path; valid path search r2-120 succeeded",
        "r2-124": "short f48 token was ambiguous; log identified f48fca0e",
    },
})

claims = [
    ("B01", "LOCAL_PASS", ["r2-109-final-domain"], "Controlled loopback raw3/ACK2/rejected1 and FAILED-only Host closure. No external provider, Mu bundle, actual or formal authority."),
    ("B02", "LOCAL_PASS", ["r2-109-final-domain"], "Valid positive first gate plus 24 isolated invalid marker/subject/route/stage/ledger cases."),
    ("B03", "LOCAL_PASS", ["r2-109-final-domain"], "Unknown route, malformed TOOL and second MODEL remain UNKNOWN; complete arbitrary wire-byte corpus not claimed."),
    ("B04", "LOCAL_PASS", ["r2-109-final-domain"], "Positive seed uses TOOL Object arguments; PREPARED/STARTED/CONFIRMED/FAILED/UNKNOWN/compensated and ledger history are separately mutated."),
    ("B05", "LOCAL_PASS_WITH_LIMIT", ["r2-110-final-adapter"], "Protected Everyone direct/inherited ACL and source-file denial, reparse ancestor, create-new, write and sync failure tested. All race schedules cannot be exhaustively established."),
    ("B06", "PARTIAL", ["r2-109-final-domain"], "Live fourth effect and late MODEL auxiliary disqualify; blocked MODEL broker returns UNKNOWN. Exact 15-second bounded drain timeout lacks deterministic in-scope fault injection."),
    ("B07", "LOCAL_PASS", ["r2-030-original-queue-with-mu", "r2-109-final-domain"], "Registry and blocked broker rejection paths covered; no universal goroutine-lifetime proof."),
    ("B08", "LOCAL_PASS", ["r2-109-final-domain"], "Raw stdout/stderr/bridge and required stopped/drained/cleanup/output/identity fields independently changed or removed."),
    ("B09", "LOCAL_PASS", ["r2-030-original-queue-with-mu"], "Complete base-f48 ordinary Mu queue tests restored byte-for-byte before appended registry tests; original 3 suites and 2 registry tests ran with frozen local bundle, zero skips."),
    ("B10", "LOCAL_PASS", ["r2-109-final-domain"], "20 exact transaction writer/Commit fault cuts roll back; positive validates five versions and forbidden-table census; exact closure replay returns zero delta, wrong subject/marker refused."),
    ("B11", "LOCAL_PASS", ["r2-109-final-domain"], "Frozen-plan heartbeat mutation cannot terminalize; first cause stays preserved while later observations disqualify."),
    ("B12", "LOCAL_PASS", ["r2-109-final-domain"], "Seventeen source/proof/marker/receipt/request/history tamper cuts, raw Host fact change, Owner grant deletion and Owner revocation rejected."),
]
save("claim-test-matrix.json", {
    "schema": "researchos.qualification-failure-B-r2-claim-test-matrix.v1",
    "scope": "candidate local/fixture evidence only; independent review pending",
    "findings": {
        "B-F01": {"candidate_resolution": "native owner/DACL/ACE/handle checks", "evidence": ["r2-110-final-adapter"]},
        "B-F02": {"candidate_resolution": "base-f48 original queue content restored and registry appended", "evidence": ["r2-030-original-queue-with-mu"]},
        "B-F03": {"candidate_resolution": "exact MODEL history/request/receipt/raw Host fact binding sealed and recomputed", "evidence": ["r2-109-final-domain"]},
    },
    "claims": [{"id": id, "status": status, "evidence": evidence, "limit": detail} for id, status, evidence, detail in claims],
    "formal_increment": 0,
    "actual_authority": False,
    "self_acceptance": False,
})

source_hashes = {path: digest(SOURCE / path) for path in NINE}
patches = {
    "delta_exact_five_from_75e5257c": {"path": "delta-exact-five-from-75e5257c.patch", **digest(ROOT / "delta-exact-five-from-75e5257c.patch"), "source_paths": FIVE},
    "whole_nine_from_f48fca0e": {"path": "whole-nine-from-f48fca0e.patch", **digest(ROOT / "whole-nine-from-f48fca0e.patch"), "source_paths": NINE},
}
save("FINAL-manifest.json", {
    "schema": "researchos.qualification-failure-B-r2-source-final.v1",
    "base_commit": "75e5257c19b2e21e6cabd5e912e2ac6a3e2fe603",
    "combined_base": "f48fca0e",
    "commit": "1d3cc504da79df5bf0f69755011738d5adb827b0",
    "tree": "be0c58bc3d0d103434663d53bf4b03d94ad25580",
    "branch": "codex/qualification-failure-b-r2-20261015",
    "worktree": str(SOURCE),
    "source_allowlist": FIVE,
    "combined_source_paths": NINE,
    "source_hashes": source_hashes,
    "patches": patches,
    "command_index": "command-index.json",
    "diagnostic_ledger": "diagnostic-ledger.json",
    "claim_test_matrix": "claim-test-matrix.json",
    "passing_native_exit_zero": ["r2-030-original-queue-with-mu", "r2-109-final-domain", "r2-110-final-adapter", "r2-111-diff-check", "r2-125-format", "r2-129-status"],
    "explicit_gap": "B06 exact bounded broker-drain timeout was not deterministically fault-injected; blocked MODEL and late suffix have distinct tests.",
    "formal_increment": 0,
    "actual_authority": False,
    "independent_review": "PENDING",
    "self_acceptance": False,
})

(ROOT / "FINAL.md").write_text(
    "# Qualification failure B revision 02 — Source candidate\n\n"
    "Commit `1d3cc504da79df5bf0f69755011738d5adb827b0` freezes exactly five revised Source/test paths. "
    "The original ordinary Mu queue tests were restored and passed with the frozen local bundle. "
    "The protected ACL, MODEL fact/request/receipt binding, first-gate seed, native terminal predicates, rollback, and exact replay cuts passed locally.\n\n"
    "The separate delta-five and combined whole-nine patches are included with explicit path lists and SHA-256 hashes in `FINAL-manifest.json`. "
    "B06's exact 15-second bounded-drain timeout remains unproven by deterministic in-scope fault injection. "
    "All evidence is local candidate evidence; independent review remains required. Formal increment: 0; actual authority: false.\n",
    encoding="utf-8",
)
print(json.dumps({"commands": len(commands), "failed_native_exits": len(failed), "patches": patches, "source_hashes": source_hashes}, ensure_ascii=False))
