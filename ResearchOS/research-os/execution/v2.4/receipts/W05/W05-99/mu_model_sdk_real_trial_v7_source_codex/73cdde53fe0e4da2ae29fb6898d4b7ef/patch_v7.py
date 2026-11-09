"""Narrow v6→v7 Source revision. No product import or execution."""
import ast
import hashlib
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path('D:/作品集/ResearchOS/research-os')
V6 = ROOT / 'execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v6_source_codex/e8d350ed0ed34a2c939f8cb894de2feb'
HERE = ROOT / 'execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v7_source_codex/73cdde53fe0e4da2ae29fb6898d4b7ef'
source = (V6 / 'mu_sdk_trial.v6.graph.proposed.py').read_text(encoding='utf-8')
changes = []


def plan(name, old, new):
    changes.append((name, old, new))


plan('typed Artifact hash syntax import', 'import os\n', 'import os\nimport re\n')
plan('terminal snapshot Goal and Run', '''            execution.get("session_id") == summary.get("session_id") ==
            final_snapshot.get("session_id"),
''', '''            execution.get("session_id") == summary.get("session_id") ==
            final_snapshot.get("session_id") and
            final_snapshot.get("goal_id") == execution.get("goal_id") and
            final_snapshot.get("active_run_id") == execution.get("run_id"),
''')
plan('typed available Artifact stream', '''    artifacts = {event["payload"].get("artifact_ref", {}).get("id")
                 for event in events if event.get("kind") == "ARTIFACT" and
                 event.get("run_id") == execution["run_id"] and
                 event["payload"].get("availability") == "AVAILABLE" and
                 isinstance(event["payload"].get("artifact_ref"), dict)}
    require(set(report["result_artifact_ids"]).issubset(artifacts),
            "CLI_TERMINAL_RESULT_ARTIFACT_EVENT_ABSENT")
    return summary, {"original_jsonl_records": len(parsed),
                     "session_event_count": len(parsed) - 1,
                     "initial_cursor": cursor - (len(parsed) - 1),
                     "final_cursor": cursor}
''', '''    artifacts = {}
    for event in events:
        if (event.get("kind") != "ARTIFACT" or
                event.get("run_id") != execution["run_id"] or
                event["payload"].get("availability") != "AVAILABLE"):
            continue
        ref = event["payload"].get("artifact_ref")
        require(isinstance(ref, dict) and set(ref) ==
                {"entity_type", "id", "revision", "content_hash"} and
                ref["entity_type"] == "Artifact" and
                isinstance(ref["id"], str) and ref["id"] and
                type(ref["revision"]) is int and ref["revision"] > 0 and
                isinstance(ref["content_hash"], str) and
                re.fullmatch(r"sha256:[0-9a-f]{64}", ref["content_hash"]),
                "CLI_ARTIFACT_ENTITY_REF_INVALID")
        require(ref["id"] not in artifacts or artifacts[ref["id"]] == ref,
                "CLI_ARTIFACT_REF_CONFLICT")
        artifacts[ref["id"]] = ref
    require(set(report["result_artifact_ids"]).issubset(artifacts),
            "CLI_TERMINAL_RESULT_ARTIFACT_EVENT_ABSENT")
    return summary, {"original_jsonl_records": len(parsed),
                     "session_event_count": len(parsed) - 1,
                     "initial_cursor": cursor - (len(parsed) - 1),
                     "final_cursor": cursor,
                     "result_artifact_refs": {identity: artifacts[identity]
                                              for identity in report["result_artifact_ids"]}}
''')
plan('graph typed stream argument', '''def verify_ordinary_goal_graph(db, doc, before, original_summary, prior_snapshot,
                               admitted, draft_policies):''', '''def verify_ordinary_goal_graph(db, doc, before, original_summary, prior_snapshot,
                               admitted, draft_policies, stream_evidence):''')
plan('graph original version and current ref', '''    for identity in ids:
        artifact = object_by_id(db, "Artifact", identity, project)
        require(artifact.get("id") == identity,
                "original host artifact absent from this project")
''', '''    refs = stream_evidence.get("result_artifact_refs")
    require(isinstance(refs, dict) and set(refs) == set(ids),
            "original typed Artifact stream differs from host result IDs")
    for identity in ids:
        reference = refs[identity]
        historical = object_by_ref(db, project, reference, "Artifact")
        require(historical.get("id") == identity and
                reference == exact_artifact_ref(db, project, identity),
                "original Artifact version/hash differs from current exact result")
''')
plan('main graph gets original stream evidence', '''        new_goal_id, task_id, run_id, policies = verify_ordinary_goal_graph(
            db, doc, before, original_summary, prior_snapshot, admitted, draft_policies)
''', '''        stream_evidence = run_invocation["consumed_file_transition"]["context_evidence"]["stream_evidence"]
        new_goal_id, task_id, run_id, policies = verify_ordinary_goal_graph(
            db, doc, before, original_summary, prior_snapshot, admitted,
            draft_policies, stream_evidence)
''')

counts = {name: source.count(old) for name, old, _ in changes}
print(counts)
if any(value != 1 for value in counts.values()):
    raise SystemExit(2)
candidate = source
for _, old, new in changes:
    candidate = candidate.replace(old, new, 1)
ast.parse(candidate)
inverse = candidate
for _, old, new in reversed(changes):
    assert inverse.count(new) == 1
    inverse = inverse.replace(new, old, 1)
assert inverse == source
raw = candidate.encode('utf-8')
with (HERE / 'mu_sdk_trial.v7.proposed.py').open('xb') as out:
    out.write(raw)
print({'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw),
       'AST_OK': True, 'inverse_exact': True})
