import sys
sys.dont_write_bytecode = True
import ast
import copy
import difflib
import hashlib
import json
import traceback
import types
from pathlib import Path

BASE=Path(__file__).resolve().parent
O=BASE/"revision"
O.mkdir(exist_ok=False)
B=BASE.parent.parent
Q=B/"native_migration_controller_temp_env_revision_codex/e6a4d23ff0a84a6d9c2905181d97c2e4"
S=B/"native_migration_atomic_publication_revision_codex/1a11d9c912f7c13799a37e93"
E=B/"native_migration_broker_temp_revision_codex/9beca53ced874c93a6101f451eb33491"
G=B/"t7_actual_failure_independent_review_codex/a765019dd7124e9fb6d389a3c213edbc/inputs/sources/source_read_guard.py"
KEY="RESEARCHOS_NATIVE_MIGRATION_HARNESS_TEMP_ROOT"

def ref(p):
    p=Path(p)
    raw=p.read_bytes()
    return {"path":str(p),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def exact(p,sha,size):
    r=ref(p)
    assert (r["sha256"],r["bytes"])==(sha,size), str(p)
    return r
def plain(r):
    return {k:r[k] for k in ("path","sha256","bytes")}
def walk(o):
    if isinstance(o,dict):
        if {"path","sha256","bytes"}.issubset(o):
            yield plain(o)
        for v in o.values():
            yield from walk(v)
    elif isinstance(o,list):
        for v in o:
            yield from walk(v)
def write(n,value):
    p=O/n
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("xb") as f:
        f.write((json.dumps(value,ensure_ascii=False,indent=2)+"\n").encode("utf-8"))
    return ref(p)
def dedup(refs):
    found={}
    for r in refs:
        k=str(Path(r["path"])).casefold()
        if k in found:
            assert found[k]["sha256"]==r["sha256"] and found[k]["bytes"]==r["bytes"]
        else:
            found[k]=plain(r)
    return list(found.values())
def topdefs(tree):
    return {n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
def assigned(tree,name):
    return next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets))

def main():
    anchors=[
        exact(Q/"HDF.json","089068f4ffe780c6553e40ddb79fee868f033bb2ba9aa9b872d066b371c65163",6890),
        exact(Q/"MF.json","6869d577ec8429c4f217bc429d4350ef24eab7831f08ee874052a2cdc8652e32",12643),
        exact(G,"e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85",11404),
    ]
    gbytes=G.read_bytes()
    assert hashlib.sha256(gbytes).hexdigest()==anchors[-1]["sha256"]
    gm=types.ModuleType("independent_ctl3_source_guard")
    exec(compile(gbytes,str(G),"exec"),gm.__dict__)
    guards=[]
    observations=[]
    try:
        boot=gm.SourceReadGuard()
        guards.append(boot)
        boot.acquire(anchors)
        hdf=json.loads(boot.get_buffer(str(Q/"HDF.json")))
        mf=json.loads(boot.get_buffer(str(Q/"MF.json")))
        assert len(mf["members"])==31
        refs=anchors+list(walk(mf["members"]))+list(walk(hdf))
        stage=gm.SourceReadGuard()
        guards.append(stage)
        stage.acquire(dedup(refs))
        sg=json.loads(stage.get_buffer(str(Q/"source-guard-closure.json")))
        refs+=list(walk(sg))
        ctl2mf=json.loads(stage.get_buffer(str(S/"MF.json")))
        envmf=json.loads(stage.get_buffer(str(E/"MF.json")))
        ctl2_locators=[]
        for relative,item in ctl2mf["members"].items():
            actual={"path":str(S/relative),"sha256":item["sha256"],"bytes":item["bytes"]}
            refs.append(actual)
            ctl2_locators.append({"manifest_relative":relative,"declared_path":item["path"],"resolved_public_ref":actual})
        refs+=list(walk(envmf["members"]))
        history=json.loads(stage.get_buffer(str(Q/"filetime-history-qualification.json")))
        refs+=list(walk(history))
        refs=dedup(refs)
        closure=gm.SourceReadGuard()
        guards.append(closure)
        closure.acquire(refs)
        def raw(p):
            return closure.get_buffer(str(p))
        def obj(p):
            return json.loads(raw(p))
        for i,r in enumerate(refs):
            dest=O/"public-inputs"/(str(i).zfill(3)+"-"+Path(r["path"]).name)
            dest.parent.mkdir(parents=True,exist_ok=True)
            with dest.open("xb") as f:
                f.write(raw(r["path"]))
        source=raw(Q/"root_native_migration_controller.py").decode("utf-8")
        base=raw(S/"root_native_migration_controller.py").decode("utf-8")
        compile(source,str(Q/"root_native_migration_controller.py"),"exec")
        ct,bt=ast.parse(source),ast.parse(base)
        cdefs,bdefs=topdefs(ct),topdefs(bt)
        assert set(cdefs)-set(bdefs)=={"_require_isolated_temp_environment"}
        assert set(bdefs)-set(cdefs)==set()
        same=[]
        for name,bnode in bdefs.items():
            if name=="context":
                continue
            cnode=cdefs[name]
            assert ast.dump(bnode,include_attributes=False)==ast.dump(cnode,include_attributes=False),name
            assert ast.get_source_segment(base,bnode)==ast.get_source_segment(source,cnode),name
            same.append(name)
        assert len(same)==30
        old_env=ast.literal_eval(assigned(bt,"ENV_KEYS"))
        new_env=ast.literal_eval(assigned(ct,"ENV_KEYS"))
        assert new_env-old_env=={KEY} and old_env-new_env==set()
        context=copy.deepcopy(cdefs["context"])
        optional=ast.parse('if "'+KEY+'" in env:\n    _require_isolated_temp_environment(env)\n').body[0]
        matches=[n for n in context.body if ast.dump(n,include_attributes=False)==ast.dump(optional,include_attributes=False)]
        assert len(matches)==1
        context.body.remove(matches[0])
        assert ast.dump(context,include_attributes=False)==ast.dump(bdefs["context"],include_attributes=False)
        clines,blines=source.splitlines(keepends=True),base.splitlines(keepends=True)
        changes=[x for x in difflib.SequenceMatcher(a=blines,b=clines,autojunk=False).get_opcodes() if x[0]!="equal"]
        assert len(changes)==3 and all(x[0]=="insert" for x in changes)
        inverse=clines[:]
        for op,i1,i2,j1,j2 in reversed(changes):
            inverse[j1:j2]=blines[i1:i2]
        assert "".join(inverse).encode("utf-8")==raw(S/"root_native_migration_controller.py")
        declared_inverse=obj(Q/"controller-inverse-edits.json")
        assert [(x["operation"],x["base_start_line_zero_based"],x["base_end_line_exclusive"],x["candidate_start_line_zero_based"],x["candidate_end_line_exclusive"]) for x in declared_inverse["edits"]]==changes
        for row in declared_inverse["edits"]:
            assert "".join(clines[row["candidate_start_line_zero_based"]:row["candidate_end_line_exclusive"]])==row["candidate_text"]
        helper=ast.get_source_segment(source,cdefs["_require_isolated_temp_environment"])
        assert helper.index("contains(trial, declared)")<helper.index("canonical_path(str(local))")<helper.index("canonical_path(proof)")
        assert 'env["TEMP"] != proof or env["TMP"] != proof' in helper
        assert all(s not in helper for s in (".read_bytes(", ".read_text(", ".open(", ".iterdir(", ".glob(", ".rglob(", "import ", "os.environ"))
        assert 'env = dict(c["cfg"]["Environment"])' in ast.get_source_segment(source,cdefs["serve"])
        assert "os.environ" not in source
        prereq=obj(Q/"root-public-context-prerequisites.json")
        assert len(prereq["exact_config_fields"])==12
        assert len(prereq["eight_public_ref_fields"])==8
        assert len(prereq["seven_harness_RawPin_fields"])==7
        con=cdefs["context"]
        cfgset=next(n.value for n in con.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="expected" for t in n.targets))
        assert set(prereq["exact_config_fields"])==ast.literal_eval(cfgset)
        for names in (prereq["eight_public_ref_fields"],prereq["seven_harness_RawPin_fields"]):
            assert any(isinstance(n,ast.For) and isinstance(n.iter,ast.Tuple) and list(ast.literal_eval(n.iter))==names for n in con.body)
        matrix=obj(Q/"boundary-matrix.json")
        assert len(matrix["cases"])==16 and all(x["actual"]=="NOT_RUN" for x in matrix["cases"])
        assert matrix["helper_called"] is False and matrix["pure_context_called"] is False
        held_invocation=obj(Q/"inputs/history/test.invocation.json")
        assert str(held_invocation["result"]["creation_time_100ns"])==history["held_native_go_FILETIME_decimal"]=="134359787460741284"
        assert history["recorded835_go_FILETIME_decimal_inaccurate"]=="134359787460741280"
        assert history["rehearsal_value_provenance"]=="Root CTL3 task text; child invocation not opened by this Source author"
        evidence={
            "schema":"researchos.independent-ctl3-source-review.v1",
            "decision":"SOURCE_ACCEPTED_PENDING_ROOT_FRESH_CONTEXT_AND_ACTUAL",
            "authority":"NONE","formal_acceptance":False,
            "candidate_ref":hdf["candidate_ref"],"CTL2_base_ref":hdf["CTL2_base_ref"],
            "held_public_ref_count":len(refs),"manifest_counts":{"CTL3":31,"CTL2":len(ctl2mf["members"]),"EnvSource":len(envmf["members"])},
            "exact_inverse_recovers_entire_CTL2":True,"changed_regions":[list(x) for x in changes],
            "unchanged_other_definitions_raw_and_AST":same,
            "context_AST_after_optional_guard_removal_equals_CTL2":True,
            "only_added_ENV_KEY":KEY,
            "compile_to_code_and_AST":"PASSED_STATIC_ONLY",
            "controller_imported":False,"context_called":False,"helper_called":False,"observer_imported":False,
            "source_observations":[
                "Context keeps unknown-key, value string/NUL, required Windows/temp keys before new optional guard",
                "Proof is a nonempty absolute existing canonical directory strictly below fixed R/.local",
                "Proof/TEMP/TMP require literal string equality; proof cannot silently derive from TEMP or inherited configuration",
                "Original trial lexical overlap in both ancestor directions rejected before proof resolve/stat",
                "Canonical local/proof comparison rejects resolved alias changes; physical containment and trial overlap checked again",
                "SystemRoot/WINDIR must be canonical existing directories; either ancestor direction with proof rejected",
                "Helper uses directory metadata only, no content reads or enumeration; no controller/helper execution during review",
                "No-proof context follows prior AST; this is backward context compatibility, not permission for fresh broker without proof",
                "Worker copies fixed cfg.Environment; separate EnvSource forwards only four public broker keys",
                "Remaining provenance/compiler/frozen input/Owner/sign/release/privatepipe/atomic publication/Jobs gates remain byte-identical",
            ],
            "boundary_case_names":[x["case"] for x in matrix["cases"]],
            "boundary_actual":"NOT_RUN",
            "config_mapping_counts":{"fixed_fields":12,"public_refs":8,"harness_RawPins":7},
            "context_frozen_compiler_resource_closure":"PENDING_ROOT_FRESH_ACTUAL",
            "Root_next":[
                "Root uses a fresh fixed cfg pin and ControllerSource matching executing __file__",
                "Hold complete public SourceReadGuard/FrozenInputs closure including all compiler, embed, product and actual runtime resources",
                "Fresh canonical temp directory owned by Root below R/.local; exact proof==TEMP==TMP and real public system directory values",
                "Run and record authorized public context validation and relevant boundary evidence; Source matrix remains NOT_RUN",
                "Fresh compile of accepted EnvSource; two exact component selectors/all 28 leaves; only then one Root-owned manual positive",
                "Manual per-payload signing, specific release, Jobs closure and independent actual acceptance remain required",
            ],
            "history":{"go_reported_inaccurate":"134359787460741280","go_native_observed":"134359787460741284","rehearsal_root_reported_actual":"134359787476336016","rehearsal_not_read_for_this_CTL3_review":True,"835_841_843_846_and_other_history_not_reset":True},
            "Source_author_closure_label":"public hash-reference closure only; not accepted as Root actual retained-context guard evidence",
            "new_mechanical_errors":1,"Main_canonical_old_Source_writes":False,
            "Go_native_SQL_sign_model_network_private_payload_execution_or_reads":False,
            "stop":True,
        }
        write("source-check.json",evidence)
        write("input-pins.json",refs)
        write("CTL2-manifest-locators.json",ctl2_locators)
        current=[(r,ref(r["path"])) for r in refs]
        drift=[r["path"] for r,a in current if (a["sha256"],a["bytes"])!=(r["sha256"],r["bytes"])]
        path_mismatches=[r["path"] for r,a in current if str(Path(a["path"])).casefold()!=str(Path(r["path"])).casefold()]
        spelling=[{"declared":r["path"],"canonical_spelling":a["path"],"same_Windows_path":True,"sha_bytes_equal":True} for r,a in current if r["path"]!=a["path"]]
        assert not drift and not path_mismatches
        write("no-drift.json",{"checked":len(refs),"sha_bytes_drift":drift,"canonical_path_mismatches":path_mismatches,"path_spelling_qualifications":spelling})
    finally:
        for g in reversed(guards):
            observations.append(g.close())
        write("guard-closure.json",observations)
    assert all(x["verification"]=="PASSED" and x["closed"] and x["retained_handles_count"]==0 and not x["errors"] for x in observations)
    print(json.dumps({"decision":evidence["decision"],"source_check_ref":ref(O/"source-check.json"),"held_public_refs":len(refs),"all_guards_closed":True,"new_mechanical_errors":1},ensure_ascii=False))
code=0
try:
    main()
except Exception:
    traceback.print_exc()
    code=1
finally:
    print("ROOT_PYTHON_EXIT="+str(code))
sys.exit(code)
