"""Create a separate Source v2; immutable Source v1 remains intact."""
import difflib
import hashlib
import json
from pathlib import Path

OLD=Path(__file__).resolve().parent
NEW=OLD.parent.parent/'checkpoint_r368_restored21_v2_source_root/cp368-w05v2-20261009'
NEW.mkdir(parents=True,exist_ok=False)
changes=[]
def rewrite(name,spans):
    before=(OLD/name).read_bytes();text=before.decode()
    for old,new in spans:
        assert text.count(old)==1,(name,old)
        text=text.replace(old,new,1)
    after=text.encode()
    with (NEW/name).open('xb') as f:f.write(after)
    assert before==after.decode().replace(spans[-1][1],spans[-1][0],1).encode() if len(spans)==1 else True
    inverse=after.decode()
    for old,new in reversed(spans):
        assert inverse.count(new)==1
        inverse=inverse.replace(new,old,1)
    assert inverse.encode()==before
    changes.append(dict(path=name,before_sha256=hashlib.sha256(before).hexdigest(),before_bytes=len(before),after_sha256=hashlib.sha256(after).hexdigest(),after_bytes=len(after),spans=[dict(before=a,after=b) for a,b in spans],complete_byte_inverse=True))
    return list(difflib.unified_diff(before.decode().splitlines(True),after.decode().splitlines(True),fromfile=str(OLD/name),tofile=str(NEW/name)))
delta=[]
delta+=rewrite('register_cp368.source.py',[
    ("    c.update(expected_previous_revision=367,revision=368,updated_at=facts['created_utc'],updated_by=ACTOR,note=facts['checkpoint_note'])", "    c['work_in_progress']['root_next_failure_ordinal_live']=live['next_original_failure_ordinal']\n    c['work_in_progress']['later_diagnostics_observed_after_cutoff']=copy.deepcopy(live['pending'])\n    c.update(expected_previous_revision=367,revision=368,updated_at=facts['created_utc'],updated_by=ACTOR,note=facts['checkpoint_note'])"),
    ("inverse_c['workers']=copy.deepcopy(old_c['workers']);del inverse_c['work_in_progress']['mu_sdk_r368']", "inverse_c['workers']=copy.deepcopy(old_c['workers']);inverse_c['work_in_progress']=copy.deepcopy(old_c['work_in_progress'])")])
origin="dict(path=str((B/'checkpoint_r368_w05_independent_review_codex/cp368r-01a11fea/failure953.original-tool-io.json').resolve(strict=True)),sha256='5526df6a460b1541612533ba44dca285bb756180568d1cc5766efb13d11f0015',bytes=1375)"
delta+=rewrite('build_source.root.py',[
    ("next_original_failure_ordinal=953,pending=[])","next_original_failure_ordinal=954,pending=[dict(ordinal=953,origin_ref="+origin+",description='Original independent Source read c3b898 guessed one missing filename; outer1, Python/Native/model NULL; original evidence preserved.')])"),
    ("N/'source-controls.json')", "N/'source-controls.json',N/'v1-to-v2.diff',N/'source-byte-inverse.json')")])
with (NEW/'v1-to-v2.diff').open('x',encoding='utf-8',newline='') as f:f.writelines(delta)
with (NEW/'source-byte-inverse.json').open('x',encoding='utf-8') as f:json.dump(dict(schema='researchos.root-cp368-source-byte-inverse.v1',reason='Update shared live diagnostic fields so Canon readers do not inherit obsolete live952; preserve historical r367 fields and Sourcecut952.',v1_handoff_ref=dict(path=str((OLD/'HDF.json').resolve()),sha256='f66d684e007a71a77e42f040b02de916053258e0fafb6aa58205f78c55ddabc3',bytes=2173),v1_manifest_ref=dict(path=str((OLD/'MF.json').resolve()),sha256='c910cdd4677d6ceeb3e9260f26918e5203ed935139fcac91aca175a7ea211fb9',bytes=2506),changes=changes,complete_inverse=True),f,ensure_ascii=False,indent=2)
print(json.dumps(dict(new_Source_namespace=str(NEW),complete_inverse=True,actual_executed=False),ensure_ascii=False))
