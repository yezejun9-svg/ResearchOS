from pathlib import Path
import ast,copy,difflib,hashlib,json
O=Path(__file__).resolve().parent
P=O.parents[1]
OLD=P/"mu_sdk_job_observer_revision_v3_codex/7a43feff8ec24250b87d04d0e346a52e"
REVIEW=P/"mu_sdk_controller_v5_independent_review_codex/ca1965e9f0b449b786c4e6925d7018fb"
AUTHOR="codex:/root/w05_merge_review"
def require(ok,message):
    if not ok: raise ValueError(message)
def meta(path):
    raw=path.read_bytes()
    return dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def write(name,value):
    path=O/name
    require(not path.exists(),"output exists "+name)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes((json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode("utf-8"))
    return meta(path)
oldpath=OLD/"mu_sdk_job_observer.v3.proposed.py"
oldraw=oldpath.read_bytes()
require(meta(oldpath)["sha256"]=="00ddbaf68bad97e607eeb491aa15205a22104890b05e2dd31d7a64ef18621d96","old source pin")
old=oldraw.decode("utf-8")
oldtree=ast.parse(old)
oldgate=next(x for x in oldtree.body if isinstance(x,ast.FunctionDef) and x.name=="validate_source_review")
lines=old.splitlines(keepends=True)
oldsegment="".join(lines[oldgate.lineno-1:oldgate.end_lineno])
policy='''SOURCE_PROVENANCE_SCHEMA = "researchos.mu-sdk-source-author-provenance.v1"
SOURCE_AUTHOR_POLICY = (
    ("controller", "controller_source", ("codex:/root/live_resource_lookup",)),
    ("observer", "observer_source", ("codex:/root/w05_merge_review",)),
    ("hooks", "hooks_source", ("codex:/root",)),
    ("phase_worker", "phase_worker_source", ("codex:/root",)),
    ("runner", None, ("codex:/root",)),
    ("canonical_transactions", "canonical_transactions_source", ("codex:/root",)),
    ("job_watchdog", "job_watchdog_source", ("codex:/root",)),
    ("source_guard", "source_guard_source", ("codex:/root/live_resource_lookup",)),
    ("base_owned", "base_owned_process_source", ("codex:/root",)),
    ("cleanup_producer", "cleanup_producer_source", ("codex:/root/live_resource_lookup",)),
    ("python_binary", "python_binary", ()),
)
'''
replacement='''def source_author_provenance(context):
    """Build provenance from fixed actual-author policy and the locked source context."""
    sources = {}
    for role, key, authors in SOURCE_AUTHOR_POLICY:
        pin = RUNNER_REF if key is None else context[key]
        require(type(pin) is dict and set(pin) == {"path", "sha256", "bytes"} and
                type(pin["path"]) is str and bool(pin["path"]) and
                type(pin["sha256"]) is str and len(pin["sha256"]) == 64 and
                all(c in "0123456789abcdef" for c in pin["sha256"]) and
                type(pin["bytes"]) is int and pin["bytes"] >= 0,
                "source provenance requires an exact three-key pin: " + role)
        sources[role] = {"source_ref": dict(pin), "authors": list(authors)}
    return {"schema": SOURCE_PROVENANCE_SCHEMA, "sources": sources}


def validate_source_review(review, context):
    excluded_authors = {actor for _, _, authors in SOURCE_AUTHOR_POLICY for actor in authors}
    require(review.get("schema") == "researchos.mu-sdk-controller-observer-independent-source-review.v2" and
            review.get("decision") == "READY_SOURCE_ONLY" and
            type(review.get("actor_id")) is str and bool(review["actor_id"]) and
            review["actor_id"] not in excluded_authors | {ROOT_ACTOR, AUTHOR, ACTOR} and
            review.get("controller_source_ref") == context["controller_source"] and
            review.get("observer_source_ref") == context["observer_source"] and
            review.get("hooks_source_ref") == context["hooks_source"] and
            review.get("runner_source_ref") == RUNNER_REF and
            review.get("phase_worker_source_ref") == context["phase_worker_source"] and
            review.get("python_binary_ref") == context["python_binary"] and
            review.get("cleanup_producer_source_ref") == context["cleanup_producer_source"] and
            review.get("source_provenance") == source_author_provenance(context) and
            review.get("callback_contract") == "REAL_ASSIGNED_SUSPENDED_FRAME_BEFORE_FIRST_RESUME" and
            review.get("formal_acceptance") is False,
            "independent source review missing or wrong source tuple")
'''
newline="\r\n" if "\r\n" in old else "\n"
policy=policy.replace("\n",newline)
replacement=replacement.replace("\n",newline)
anchor='ROOT_ACTOR = "codex:/root"'+newline
require(old.count(anchor)==1 and old.count(oldsegment)==1,"unique source anchors")
new=old.replace(anchor,anchor+policy,1).replace(oldsegment,replacement,1)
newpath=O/"mu_sdk_job_observer.v4.proposed.py"
require(not newpath.exists(),"new source exists")
newpath.write_bytes(new.encode("utf-8"))
newtree=ast.parse(new)
require(new.replace(anchor+policy,anchor,1).replace(replacement,oldsegment,1).encode("utf-8")==oldraw,"inverse byte identity")
added_names={"SOURCE_PROVENANCE_SCHEMA","SOURCE_AUTHOR_POLICY"}
def normalize(tree):
    keep=[]
    for n in tree.body:
        if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in added_names for t in n.targets): continue
        if isinstance(n,ast.FunctionDef) and n.name=="source_author_provenance":continue
        keep.append(oldgate if isinstance(n,ast.FunctionDef) and n.name=="validate_source_review" else n)
    return ast.dump(ast.Module(body=keep,type_ignores=[]),include_attributes=False)
require(normalize(newtree)==ast.dump(oldtree,include_attributes=False),"unrelated AST changed")
oldfuncs={n.name:ast.get_source_segment(old,n) for n in oldtree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
newfuncs={n.name:ast.get_source_segment(new,n) for n in newtree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
require(all(newfuncs[k]==v for k,v in oldfuncs.items() if k!="validate_source_review"),"unrelated source function changed")
const={}
for n in newtree.body:
    if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name):
        if n.targets[0].id in {"AUTHOR","ACTOR","ROOT_ACTOR","RUNNER_REF","BASE_REF","SOURCE_PROVENANCE_SCHEMA","SOURCE_AUTHOR_POLICY"}:
            const[n.targets[0].id]=ast.literal_eval(n.value)
selected=[n for n in newtree.body if isinstance(n,ast.FunctionDef) and n.name in {"require","source_author_provenance","validate_source_review"}]
scope=dict(const)
exec(compile(ast.Module(body=selected,type_ignores=[]),"<pure-source-review-gate-controls>","exec"),scope)
helper=scope["source_author_provenance"];gate=scope["validate_source_review"]
context={key:dict(path="C:/fixture/"+role+".py",sha256=hashlib.sha256(role.encode()).hexdigest(),bytes=100) for role,key,authors in const["SOURCE_AUTHOR_POLICY"] if key is not None}
context["observer_source"]=meta(newpath)
review=dict(schema="researchos.mu-sdk-controller-observer-independent-source-review.v2",decision="READY_SOURCE_ONLY",actor_id="codex:/root/command_queue_impl",controller_source_ref=context["controller_source"],observer_source_ref=context["observer_source"],hooks_source_ref=context["hooks_source"],runner_source_ref=const["RUNNER_REF"],phase_worker_source_ref=context["phase_worker_source"],python_binary_ref=context["python_binary"],cleanup_producer_source_ref=context["cleanup_producer_source"],source_provenance=helper(context),callback_contract="REAL_ASSIGNED_SUSPENDED_FRAME_BEFORE_FIRST_RESUME",formal_acceptance=False)
controls=[]
def check(name,r=None,c=None,accept=False):
    rejected=False
    try: gate(review if r is None else r,context if c is None else c)
    except (ValueError,KeyError,TypeError): rejected=True
    require(rejected != accept,"control failed "+name)
    controls.append(dict(name=name,expected="ACCEPT" if accept else "REJECT",actual="REJECT" if rejected else "ACCEPT",passed=True))
check("exact_current_tuple_and_provenance_accept",accept=True)
for actor in [None,"",0,False,[],{},const["ROOT_ACTOR"],const["AUTHOR"],const["ACTOR"],"codex:/root/live_resource_lookup"]:
    r=copy.deepcopy(review);r["actor_id"]=actor;check("reject_actor_"+repr(actor),r)
authors=["codex:/root","codex:/root/w05_merge_review","codex:/root/live_resource_lookup"]
for mask in range(8):
    for actor in authors:
        r=copy.deepcopy(review);r["actor_id"]=actor
        r["source_authors"]=[a for i,a in enumerate(authors) if mask & (1<<i)]
        r["source_author"]="unrelated-self-declaration"
        check("untrusted_author_list_mask_"+str(mask)+"_actor_"+actor,r)
for role in review["source_provenance"]["sources"]:
    for field,value in [("path","C:/different.py"),("sha256","0"*64),("bytes",777)]:
        r=copy.deepcopy(review);r["source_provenance"]["sources"][role]["source_ref"][field]=value
        check("reject_"+role+"_pin_"+field,r)
    r=copy.deepcopy(review);r["source_provenance"]["sources"][role]["authors"]=["codex:/unrelated"]
    check("reject_"+role+"_authors",r)
    r=copy.deepcopy(review);del r["source_provenance"]["sources"][role]
    check("reject_missing_role_"+role,r)
    r=copy.deepcopy(review);r["source_provenance"]["sources"][role]["extra"]=True
    check("reject_extra_role_metadata_"+role,r)
for name,mut in [
    ("missing_provenance",lambda r:r.pop("source_provenance")),
    ("wrong_provenance_schema",lambda r:r["source_provenance"].update(schema="wrong")),
    ("extra_provenance_role",lambda r:r["source_provenance"]["sources"].update(extra={})),
    ("extra_provenance_key",lambda r:r["source_provenance"].update(extra=True)),
    ("old_schema",lambda r:r.update(schema="researchos.mu-sdk-controller-observer-independent-source-review.v1")),
    ("unissued_decision",lambda r:r.update(decision=None)),
    ("callback_changed",lambda r:r.update(callback_contract="WRONG")),
    ("formal_acceptance_true",lambda r:r.update(formal_acceptance=True)),
    ("formal_acceptance_integer_zero",lambda r:r.update(formal_acceptance=0)),
]:
    r=copy.deepcopy(review);mut(r);check(name,r)
for key in ["controller_source_ref","observer_source_ref","hooks_source_ref","runner_source_ref","phase_worker_source_ref","python_binary_ref","cleanup_producer_source_ref"]:
    r=copy.deepcopy(review);r[key]=None;check("missing_explicit_"+key,r)
for role,key,authors in const["SOURCE_AUTHOR_POLICY"]:
    if key is None:continue
    for field,value in [("path",""),("sha256","not_a_hash"),("bytes",True)]:
        c=copy.deepcopy(context);c[key][field]=value
        check("malformed_context_"+role+"_"+field,c=c)
    c=copy.deepcopy(context);c[key]["extra"]=True;check("extra_context_pin_key_"+role,c=c)
    c=copy.deepcopy(context);del c[key];check("missing_context_"+role,c=c)
template=copy.deepcopy(review)
template.update(actor_id=None,decision=None,execution_grant_issued=False,note="Unissued template. Future C6 and all current helper/binary refs require one actual independent review; never infer readiness from this author template.")
for key in ["controller_source_ref","hooks_source_ref","phase_worker_source_ref","python_binary_ref","cleanup_producer_source_ref"]:template[key]=None
template["source_provenance"]["sources"]={role:dict(source_ref=meta(newpath) if role=="observer" else const["RUNNER_REF"] if role=="runner" else const["BASE_REF"] if role=="base_owned" else None,authors=list(authors)) for role,key,authors in const["SOURCE_AUTHOR_POLICY"]}
write("independent-source-review.v4.template.json",template)
write("pure-controls.v4.json",dict(schema="researchos.observer-v4-pure-author-controls.v1",method="Compile only AST-extracted require/source_author_provenance/validate_source_review with literal constants; no candidate import/entry, real WinAPI, filesystem callbacks or process/provider calls.",total=len(controls),passed=len(controls),controls=controls))
inputs=[]
paths=[oldpath,OLD/"manifest.json",OLD/"handoff.json",OLD/"independent-source-review.v3.template.json",REVIEW/"findings.json",REVIEW/"independent-source-review.json",REVIEW/"handoff.json",Path(const["RUNNER_REF"]["path"])]
for path in paths:
    ref=meta(path)
    target=O/"input-snapshots"/path.relative_to(P)
    target.parent.mkdir(parents=True,exist_ok=True)
    require(not target.exists(),"snapshot exists")
    target.write_bytes(path.read_bytes())
    ref["snapshot"]=str(target.relative_to(O))
    require(meta(target)["sha256"]==ref["sha256"],"snapshot mismatch")
    inputs.append(ref)
oldmf=json.loads((OLD/"manifest.json").read_bytes())
for ref in oldmf["members"]:
    require(meta(Path(ref["path"]))==ref,"old manifest member changed")
(O/"forward.v3-to-v4.diff").write_bytes("".join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile="observer.v3",tofile="observer.v4")).encode("utf-8"))
(O/"inverse.v4-to-v3.diff").write_bytes("".join(difflib.unified_diff(new.splitlines(True),old.splitlines(True),fromfile="observer.v4",tofile="observer.v3")).encode("utf-8"))
report=dict(schema="researchos.observer-v4-author-source-preparation.v1",decision="SOURCE_PREPARATION_ONLY_NOT_INDEPENDENT_REVIEW",source_author=AUTHOR,source_ref=meta(newpath),old_source_ref=meta(oldpath),runner_ref=const["RUNNER_REF"],inputs=inputs,changes=["fixed literal 11-role actual-author policy","pure source_author_provenance(context) helper","validate_source_review excludes every fixed actual author and pins exact provenance plus cleanup producer ref"],checks=dict(inverse_source_bytes_exact=True,unrelated_AST_unchanged=True,unrelated_function_source_bytes_unchanged=True,old_manifest_all_members_verified=True,pure_gate_controls=len(controls),source_schema_v2_unchanged=True,runner_v9_unchanged=True,candidate_module_imports=0,candidate_entry_calls=0,real_winapi_calls=0,native_jobs=0,provider_requests=0,main_or_canonical_writes=0,formal_acceptance_delta=0))
write("source-preparation.v4.json",report)
(O/"root-caller-contract.md").write_text("""# O4 Root caller contract

O4 is Source preparation only. It does not issue independent review or permission to run.
C6 and O4 use schema researchos.mu-sdk-controller-observer-independent-source-review.v2.
The existing six explicit refs remain exact, and cleanup_producer_source_ref is additionally required.
The independent record must carry source_provenance exactly equal to O4 source_author_provenance(context).
This helper is pure metadata; source bytes are checked and locked by C6 before import and before resume.

The fixed SOURCE_AUTHOR_POLICY covers 11 roles. Root, observer author w05_merge_review,
and controller/guard/cleanup author live_resource_lookup cannot independently review this bundle.
The Python binary has an exact current pin and an empty session-author list because it is upstream software.
Caller source_author/source_authors lists are never authority. Do not derive policy from review data.
The new context key cleanup_producer_source and review key cleanup_producer_source_ref must be identical.

C6 pins O4 Source; O4 derives the expected C6 pin from its already checked controller_source context,
which avoids a C6/O4 reciprocal source-hash cycle. All ten context source pins and the fixed runner
must match the same Root-owned locked current source set; replace no reference after review.
C6 must enforce the same fixed policy and exact provenance before importing any reviewed modules
and in the callback before first ResumeThread. Do not reuse an old review merely because its label is READY.

The template is intentionally unissued: actor_id and decision are null, unresolved helper refs are null.
command_queue_impl may fill an independent record only after reviewing the final C6/O4/helper/binary tuple.
No candidate execution, provider request, native process admission, product acceptance or cleanup result
is established by this source-preparation packet.
""",encoding="utf-8")
(O/"HANDOFF.md").write_text("""# O4 observer Source preparation

Prepared solely in this new immutable namespace. O3 and existing Main/canonical files remain untouched.
C5-R01 is addressed in Source by fixed actual-author exclusion and exact 11-role provenance.
The review gate additionally binds C6's cleanup producer. C5-R02 runtime cleanup implementation belongs to C6.
All unrelated observer source AST/function text and the v9 runner pin remain identical to O3.
See pure-controls.v4.json for author-side pure gate controls, source-preparation.v4.json for source
and input pins, and root-caller-contract.md for the paired C6 contract.

This is not independent READY_SOURCE_ONLY. An independent reviewer must examine the final combined
C6/O4/helper/binary source tuple. This author did not import or execute the observer candidate,
call real Windows APIs, start a native Job or contact a provider. Formal acceptance delta is zero.
Read error ddf3f6 is preserved separately once as failure-origin.705.json; its shell outer exit is 0,
and Python/native exits are NULL. The absent filename was corrected using the actual v3 template.
After sealing manifest.json and handoff.json, STOP all writes in this source namespace.
""",encoding="utf-8")
print(json.dumps(dict(source_ref=meta(newpath),controls=len(controls),report_ref=meta(O/"source-preparation.v4.json")),ensure_ascii=False))

