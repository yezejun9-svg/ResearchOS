"""Resume only unreached controls, with the actual four-field review MF shape."""
import ast, hashlib, json, types
from pathlib import Path
N=Path(__file__).resolve().parent
original=(N/'prepare_source.py').read_text(encoding='utf-8')
raw=original.replace("prior_mf=doc(prior_review['mf']['path']);prior_decision=doc(prior_review['decision']['path'])", "prior_mf_raw=doc(prior_review['mf']['path']);prior_mf=dict(prior_mf_raw,members=caller.review_member_refs(prior_mf_raw,review_base));prior_decision=doc(prior_review['decision']['path'])")
raw=raw.replace("check('syntax-and-inert-import',not any(x in sys.modules for x in ('sqlite3','_sqlite3')))", "results.extend(json.loads((N/'source-controls.json').read_bytes())['controls'])")
raw=raw.replace("check('exact-v2-leaf-source-pins',all(caller.same_ref(pin(x['path']),x) for x in leaf.values()))", "check('MF-adapter-no-SQL-inert-import',not any(x in sys.modules for x in ('sqlite3','_sqlite3')))\n        member=prior_mf_raw['members'][0]\n        for label,change in [('unknown-member-field',dict(member,unknown=True)),('escaping-member-relative',dict(member,relative_path='../outside')),('fake-member-path',dict(member,path=str(N/'wrong'))),('bad-member-bytes-bool',dict(member,bytes=True))]:\n            rejects(label,lambda change=change:caller.review_member_refs(dict(schema=prior_mf_raw['schema'],members=[change]),review_base))")
raw=raw.replace("'source-controls.guard.closed.json'", "'source-controls.revision.guard.closed.json'").replace("'source-controls.json'", "'source-controls.revision.json'")
# The two original successes are evidence reuse, not a rerun or altered receipt.
raw=raw.replace("results.extend(json.loads((N/'source-controls.revision.json').read_bytes())['controls'])", "results.extend(dict(row,reused_from_original_prefix=True) for row in json.loads((N/'source-controls.json').read_bytes())['controls'])")
raw=raw.replace("prior-review-reject-not-runtime-authority", "prior-review-reject-not-runtime-authority")
appendix=types.ModuleType('public21_preparation_text_appendix')
exec(compile((N/'revise_preparation_text.py').read_bytes(),str(N/'revise_preparation_text.py'),'exec'),appendix.__dict__)
raw=appendix.revise(raw)
m=types.ModuleType('public21_source_preparation_revision');m.__file__=str(Path(__file__).resolve())
try:
    compile(ast.parse(raw),str(Path(__file__).resolve()),'exec')
    exec(compile(raw,str(Path(__file__).resolve()),'exec'),m.__dict__)
    m.main()
    before=(N/'public21_root.before-mf-adapter.source.txt').read_bytes();after=(N/'public21_root.source.py').read_bytes()
    result=dict(schema='researchos.public21-review-MF-shape-source-revision.v1',original_Source_ref=dict(path=str(N/'public21_root.before-mf-adapter.source.txt'),sha256=hashlib.sha256(before).hexdigest(),bytes=len(before)),candidate_ref=m.pin(N/'public21_root.source.py'),prior_closed_guard_ref=m.pin(N/'source-controls.guard.closed.json'),original_99c046_preserved=True,delta_scope='strict actual Task90 relative-path MF metadata and sole accepted Task94 HDF/MF/decision/actual existing FINAL protocol; unchanged OC3/other caller gates',two_old_controls_reused_not_rerun=True)
    m.save('review-MF-shape-revision.json',result)
except BaseException:
    print('ROOT_PYTHON_EXIT=1',flush=True);raise
else:print('ROOT_PYTHON_EXIT=0',flush=True)
