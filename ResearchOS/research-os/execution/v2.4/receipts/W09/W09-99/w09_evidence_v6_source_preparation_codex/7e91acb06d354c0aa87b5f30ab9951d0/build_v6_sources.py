import ast,difflib,hashlib,json
from pathlib import Path
O=Path(__file__).parent
R=Path('D:/作品集/ResearchOS/research-os')
S=R/'execution/v2.4/receipts/W09/W09-99/w09_evidence_v5_source_preparation_codex/a1c93c361f85414db51b6aded781ab16'
REVIEW=R/'execution/v2.4/receipts/W09/W09-99/w09_evidence_v5_independent_source_review_codex/a536faec157c424787b6010f450ae56c/review.json'
def pin(p):
 b=Path(p).read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def put(n,b):
 with (O/n).open('xb') as f:f.write(b)
 return pin(O/n)
def save(n,v):return put(n,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
checks=[]
def ck(n,v):
 checks.append({'check':n,'passed':bool(v)})
 if not v:raise ValueError(n)
ck('review pin',pin(REVIEW)['sha256']=='24bfe44b459d386d7a8225eceabe187c29f34575c8503636d035eb49280493e8')
ck('v5 manifest pin',pin(S/'manifest.json')['sha256']=='89f35a999f30c4eb6edc8a90fc14e8e4947279de666ff35099111cf04dbc4026')
mf=json.loads((S/'manifest.json').read_bytes())
for r in mf['members']:
 actual=pin(r['path']);ck('v5 input '+Path(r['path']).name,actual['sha256']==r['sha256'] and actual['bytes']==r['bytes'])
h=json.loads((S/'handoff.json').read_bytes())
sources={Path(r['path']).name:Path(r['path']).read_bytes() for r in h['candidate_source_refs']}
edits={}
def change(name,old,new):
 b=sources[name];a=old.encode();z=new.encode()
 ck('unique transform '+name+' '+str(len(edits.get(name,[]))),b.count(a)==1)
 sources[name]=b.replace(a,z,1);edits.setdefault(name,[]).append((a,z))
closure='w09_evidence_closure.v5.proposed.py'
router='w09_formal_router.v5.proposed.py'
go='retrieval_test.v5.proposed.go'
change(closure,'from pathlib import Path\n','''from pathlib import Path


# These are original business-result JSON bytes, not exporter event envelopes.
A06_MANIFEST_RAW_LABELS = frozenset({
    "a06-materialize-v1-manifest",
    "a06-materialize-after-delete-manifest",
})
''')
change(closure,'if label.startswith(opaque) or re.fullmatch(r"simulated-opinion-(?:0[0-9]|1[0-9])", label):','if label.startswith(opaque) or label in A06_MANIFEST_RAW_LABELS or re.fullmatch(r"simulated-opinion-(?:0[0-9]|1[0-9])", label):')
change(router,'verify_a06, verify_mode, safe_repo_rel','verify_a06, verify_mode, safe_repo_rel, A06_MANIFEST_RAW_LABELS')
change(router,'if label.startswith(("http-request", "http-response", "file-body-", "g02-junction-stdout")) or __import__("re").fullmatch','if label.startswith(("http-request", "http-response", "file-body-", "g02-junction-stdout")) or label in A06_MANIFEST_RAW_LABELS or __import__("re").fullmatch')
change(closure,'and junction_event.get("output") == junction.get("output_pin")','and junction_event.get("output") ==\n                    witness_values["researchos.w09-junction-witness.v1"].get("output_pin")')
change(go,'''"root_id": rootID, "source_artifact_id": artifact["id"],
\t\t"authorized_snapshot_ids": bundle["authorized_snapshot_ids"]})''','''"root_id": rootID, "source_artifact_id": artifact["id"], "project_id": f.project,
\t\t"bundle": bundle, "bundle_ref": Ref(bundle, "ContextBundle"),
\t\t"authorized_snapshot_ids": bundle["authorized_snapshot_ids"]})''')
change(go,'''"root_id": rootID, "principal_id": f.owner,
\t\t"authorized_snapshot_ids": newBundle["authorized_snapshot_ids"],''','''"root_id": rootID, "principal_id": f.owner, "project_id": f.project,
\t\t"bundle": newBundle, "bundle_ref": Ref(newBundle, "ContextBundle"),
\t\t"authorized_snapshot_ids": newBundle["authorized_snapshot_ids"],''')
old='''    initial_manifest = _raw_pin(first_materialize.get("manifest"), members, test)
    later_manifest = _raw_pin(after_materialize.get("manifest"), members, test)
    require(initial_manifest and later_manifest and b"gamma deleted v3" not in later_manifest
            and first_materialize.get("target_path") != after_materialize.get("target_path")
            and stale_call.get("target_path") not in
                {first_materialize.get("target_path"), after_materialize.get("target_path")},
            "A06_MATERIALIZE_RAW_RESULT_MISSING")
'''
new='''    # Raw result labels and sequence positions identify these original calls;
    # a valid adjacent file from the same test cannot substitute for a result.
    def sequence(path):
        return int(path.name.split("-", 1)[0])

    def materialize_result(call, label, bundle_event):
        claim = call.get("manifest")
        raw = _raw_pin(claim, members, test)
        expected = [p for p in members if p.parent.name == test
                    and p.name.split("-", 1)[1] == label + ".raw"]
        require(len(expected) == 1 and Path(claim["path"]).resolve(strict=True) == expected[0],
                "A06_MATERIALIZE_EXACT_RAW_LABEL")
        value = json.loads(raw)
        bundle = bundle_event.get("bundle")
        require(isinstance(value, dict) and isinstance(bundle, dict)
                and bundle_event.get("project_id") == states[0]["project"]
                and bundle_event.get("root_id") == states[0]["root_id"]
                and bundle_event.get("principal_id") == states[0]["principal"]
                and bundle.get("project_id") == states[0]["project"]
                and bundle.get("task_id") == bundle_event["task_id"] == call["task_id"]
                and isinstance(bundle.get("id"), str) and bundle["id"]
                and type(bundle.get("revision")) is int and bundle["revision"] >= 1
                and isinstance(bundle.get("receipt_hash"), str) and bundle["receipt_hash"]
                and bundle_event.get("bundle_ref") ==
                    {"entity_type": "ContextBundle", "id": bundle["id"],
                     "revision": bundle["revision"], "content_hash": bundle["receipt_hash"]}
                and value.get("project_id") == states[0]["project"]
                and value.get("task_id") == call["task_id"]
                and value.get("bundle_ref") == bundle_event["bundle_ref"]
                and isinstance(bundle.get("version_vector"), list)
                and value.get("version_vector") == bundle["version_vector"]
                and isinstance(bundle.get("source_manifest_hash"), str)
                and value.get("source_manifest_hash") == bundle["source_manifest_hash"]
                and bundle_event.get("authorized_snapshot_ids") == bundle.get("authorized_snapshot_ids"),
                "A06_MATERIALIZE_TASK_BUNDLE_JOIN")
        # f.bundle is an actual captured POST, so its returned identity/content
        # must agree with this event and with the materialization return value.
        exchanges = [x["value"] for x in events.get("http-exchange", []) if x["test"] == test]
        matches = []
        for exchange in exchanges:
            if (exchange.get("method") == "POST" and exchange.get("status") == 201
                    and exchange.get("path") == "/v1/projects/" + states[0]["project"] + "/context-bundles"):
                request = json.loads(_raw_pin(exchange.get("request"), members, test))
                response = json.loads(_raw_pin(exchange.get("response"), members, test))
                if isinstance(request, dict) and request.get("task_id") == call["task_id"] and response == bundle:
                    matches.append(exchange)
        require(len(matches) == 1, "A06_BUNDLE_ORIGINAL_HTTP_RESULT")
        entries = value.get("input_manifest")
        require(isinstance(entries, list), "A06_MATERIALIZE_INPUT_MANIFEST")
        ids, hashes = [], {}
        for entry in entries:
            require(isinstance(entry, dict) and isinstance(entry.get("ref"), dict),
                    "A06_MATERIALIZE_INPUT_ENTRY")
            entity = entry["ref"]
            aid = entity.get("id")
            require(entity.get("entity_type") == "Artifact" and isinstance(aid, str) and aid
                    and type(entity.get("revision")) is int and entity["revision"] >= 1
                    and entry.get("path") == "inputs/" + aid + ".content"
                    and isinstance(entry.get("content_hash"), str)
                    and entity.get("content_hash") == entry["content_hash"],
                    "A06_MATERIALIZE_INPUT_ID_HASH")
            ids.append(aid)
            hashes[aid] = entry["content_hash"]
        require(len(ids) == len(set(ids)), "A06_MATERIALIZE_DUPLICATE_INPUT_ID")
        authorized = bundle["authorized_snapshot_ids"]
        require(isinstance(authorized, list) and all(isinstance(aid, str) and aid for aid in authorized)
                and len(authorized) == len(set(authorized))
                and set(authorized) <= set(ids), "A06_MATERIALIZE_AUTHORIZED_INPUT_SET")
        return value, expected[0], hashes

    initial_manifest, initial_path, initial_inputs = materialize_result(
        first_materialize, "a06-materialize-v1-manifest", initial_bundle)
    later_manifest, later_path, later_inputs = materialize_result(
        after_materialize, "a06-materialize-after-delete-manifest", new_bundle)
    original_rows = [r for r in states[1]["actual_snapshots"]
                     if r.get("root_id") == states[0]["root_id"] and r.get("relative_path") == "same.txt"
                     and r.get("content_hash") == "sha256:" + digest(
                         _raw_pin(files["initial-authorized"]["body"], members, test))]
    deleted_rows = [r for r in states[3]["actual_snapshots"]
                    if r.get("root_id") == states[0]["root_id"] and r.get("relative_path") == "same.txt"
                    and r.get("content_hash") == "sha256:" + digest(b"gamma deleted v3")]
    require(len(original_rows) == len(deleted_rows) == 1
            and initial_bundle["source_artifact_id"] == original_rows[0].get("artifact_id")
            and new_bundle["deleted_artifact_id"] == deleted_rows[0].get("artifact_id")
            and initial_inputs.get(initial_bundle["source_artifact_id"]) == original_rows[0]["content_hash"]
            and initial_bundle["source_artifact_id"] not in later_inputs
            and new_bundle["deleted_artifact_id"] not in later_inputs
            and initial_bundle["bundle_ref"] != new_bundle["bundle_ref"],
            "A06_MATERIALIZE_SNAPSHOT_EXCLUSION_JOIN")
    def event_sequence(label):
        return sequence(events[label][0]["path"])
    require(event_sequence("a06-bundle-initial") < sequence(initial_path)
            < event_sequence("a06-materialize-initial")
            < event_sequence("a06-materialize-stale-rejected")
            < event_sequence("a06-bundle-after-delete") < sequence(later_path)
            < event_sequence("a06-materialize-after-delete"),
            "A06_ORIGINAL_CALL_ORDER")
    base = Path(states[0]["root_path"]).parent
    require(first_materialize.get("target_path") == str(base / "materialized-v1")
            and after_materialize.get("target_path") == str(base / "materialized-after-delete")
            and stale_call.get("target_path") == str(base / "stale-context")
            and isinstance(stale_call.get("actual_error"), str) and stale_call["actual_error"]
            and initial_path != later_path,
            "A06_MATERIALIZE_TARGET_OR_REJECTION")
'''
change(closure,old,new)
# No native compiler/import is used. Verify every whole-file inverse first.
pairs=[];candidate=[]
for r in h['candidate_source_refs']:
 oldpath=Path(r['path']);old=oldpath.read_bytes();new=sources[oldpath.name];back=new
 for a,z in reversed(edits.get(oldpath.name,[])):
  ck('inverse unique '+oldpath.name,back.count(z)==1);back=back.replace(z,a,1)
 ck('wholebyteinverse '+oldpath.name,back==old)
 name=oldpath.name.replace('.v5.','.v6.')
 if oldpath.suffix=='.py':ast.parse(new,filename=name);ck('AST '+name,True)
 nr=put(name,new);candidate.append(nr)
 pr=None
 if old!=new:
  delta=''.join(difflib.unified_diff(old.decode().splitlines(keepends=True),new.decode().splitlines(keepends=True),fromfile='v5/'+oldpath.name,tofile='v6/'+name))
  pr=put(name+'.patch',delta.encode())
 pairs.append({'old':r,'new':nr,'whole_byte_inverse':True,'exact_copy':old==new,'diff_ref':pr,'substitutions':len(edits.get(oldpath.name,[]))})
save('source-inverse.json',{'schema':'researchos.w09-v6-source-inverse.v1','input_review_ref':pin(REVIEW),'old_manifest_ref':pin(S/'manifest.json'),'pairs':pairs,'historical_I01':'OPEN; no overwritten bytes recovered','source_or_canonical_modified':False})
save('static-audit.json',{'schema':'researchos.w09-v6-source-static-audit.v1','checks':checks,'candidate_imported':False,'candidate_executed':False,'Go_syntax_compiler_run':False,'new_failure_count':0})
print(json.dumps({'candidate_refs':candidate,'checks':len(checks),'status':'GENERATED_UNSEALED_PENDING_AUTHOR_STATIC_DATAFLOW_REVIEW'},ensure_ascii=False))

