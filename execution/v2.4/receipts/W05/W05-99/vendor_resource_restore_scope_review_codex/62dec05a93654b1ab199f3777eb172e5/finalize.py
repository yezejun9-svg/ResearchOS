import concurrent.futures, hashlib, json, subprocess
from pathlib import Path
from datetime import datetime, timezone
ROOT=Path('D:/作品集/ResearchOS/research-os'); OUT=Path(__file__).resolve().parent
def sha(raw): return hashlib.sha256(raw).hexdigest()
def ref(p): return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def write(name,data):
    with (OUT/name).open('x',encoding='utf-8',newline='\n') as f: json.dump(data,f,ensure_ascii=False,indent=2); f.write('\n')
audit=json.loads((OUT/'audit.json').read_bytes())
before=json.loads((OUT/'inventory.before.json').read_bytes())
closure=json.loads((OUT/'public_read_closure.json').read_bytes())
notes=[]; resources=[]
for row in audit['issues']:
    if row['status']=='MISSING':
        assert row['eligible_for_narrow_restore']; resources.append(row); continue
    original=(ROOT/row['original_bytes_ref']['path']).read_bytes(); current=(ROOT/row['path']).read_bytes()
    assert row['manifest_match'] and current.replace(b'\r\n',b'\n')==original and b'\r' not in original
    notes.append({'path':row['path'],'classification':'MANIFEST_MATCHING_WORKTREE_CRLF_VS_GIT_LF',
      'working_sha256':sha(current),'git_blob_sha256':sha(original),'git_blob_oid':row['git']['blob_oid'],
      'CRLF_count':current.count(b'\r\n'),'working_size':len(current),'git_size':len(original),
      'exact_CRLF_to_LF_equality':True,'restoration_required':False,'instruction':'Keep current manifest-matching bytes unchanged.'})
def check(row):
    p=ROOT/row['path']
    if row['status']=='MISSING': return {'path':row['path'],'still_absent':not p.exists() and not p.is_symlink()}
    raw=p.read_bytes(); return {'path':row['path'],'matches_original_read':sha(raw)==row['actual_sha256'],
     'matches_manifest':sha(raw)==row['expected_sha256'] and len(raw)==row['expected_size']}
with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool: current=list(pool.map(check,before))
assert all(r.get('still_absent',r.get('matches_original_read') and r.get('matches_manifest')) for r in current)
assert all(sha((ROOT/r['path']).read_bytes())==r['sha256'] for r in closure['before'])
argv=['git','check-attr','text','eol','--']+[r['path'] for r in notes]
p=subprocess.run(argv,cwd=ROOT,capture_output=True)
for ext,raw in [('stdout',p.stdout),('stderr',p.stderr)]:
    with (OUT/('git-line-ending-attributes.'+ext)).open('xb') as f:f.write(raw)
write('git-line-ending-attributes.invocation.json',{'actualargv':argv,'cwd':str(ROOT),'exit':p.returncode,
 'stdout_ref':ref(OUT/'git-line-ending-attributes.stdout'),'stderr_ref':ref(OUT/'git-line-ending-attributes.stderr')})
assert p.returncode==0
write('inventory.current.json',current)
write('git_line_ending_reconciliation.json',{'interpretation':'No modified vendor content relative to builder manifest. Six existing scripts differ only because working tree is CRLF and immutable Git blob is LF.',
 'rows':notes,'attribute_invocation_ref':ref(OUT/'git-line-ending-attributes.invocation.json')})
write('audit.final.json',{'schema':'researchos.vendor-resource-readonly-audit.v1','reviewer_id':'codex:/root/sources_parent_impl',
 'time':datetime.now(timezone.utc).isoformat(),'head':audit['head'],'manifest_ref':audit['manifest_ref'],
 'counts':{'manifest_total':5083,'manifest_matching_present':5077,'missing':6,'manifest_modified_present':0,
 'git_exact_matching_present':5071,'git_LF_worktree_CRLF_present':6},'missing_resources':resources,
 'preliminary_audit_ref':ref(OUT/'audit.json'),'reconciliation_ref':ref(OUT/'git_line_ending_reconciliation.json'),
 'current_inventory_ref':ref(OUT/'inventory.current.json'),'public_closure_ref':ref(OUT/'public_read_closure.json'),
 'mirror_ref':ref(OUT/'mirror_observation.json'),'drift':0,'resource_writes':0,'build_runs':0,
 'deletion_origin':'UNKNOWN_NOT_ATTRIBUTED','preliminary_note':'Initial MODIFIED_OR_GIT_MISMATCH categorization is refined here; it was not a finding of manifest modification.'})
proposal=json.loads((OUT/'scope_proposal.json').read_bytes())
proposal.update(status='PROPOSED_EXACT6_BINARY_RESOURCE_RESTORE_REQUIRES_ROOT_REGISTRATION',audit_ref=ref(OUT/'audit.final.json'),
 resources=resources,exact_resource_paths=[r['path'] for r in resources],
 original_preliminary_proposal_ref=ref(OUT/'scope_proposal.json'),
 preliminary_proposal_superseded=True,
 unchanged_script_notice='Six CRLF script files already match the manifest. Excluded from restore scope; Git LF blobs must not replace them.',
 mirror_source={'existing_junction':'third_party/mu/node_modules/@earendil-works/pi-coding-agent',
 'target':'third_party/mu/packages/coding-agent','only_restore_target':'third_party/mu/packages/coding-agent/docs/images/exy.png','separate_mirror_write':False})
write('scope_proposal.final.json',proposal)
write('handoff.final.json',{'status':'READONLY_EXACT6_RESTORE_SCOPE_PROPOSED','audit_ref':ref(OUT/'audit.final.json'),
 'proposal_ref':ref(OUT/'scope_proposal.final.json'),'manifest_entries':5083,'matching_present':5077,'missing':6,
 'modified_against_manifest':0,'git_line_ending_notes':6,'resource_writes':0,'build_runs':0,'private_reads':0,'network_calls':0,
 'deletion_origin':'UNKNOWN_NOT_ATTRIBUTED','source_drift':0,
 'remaining_gate':'Root registration then absent-only immutable blobs. New builder qualification remains a subsequent action.',
 'failure_origins':[],'superseded_handoff_ref':ref(OUT/'handoff.json')})
write('manifest.final.json',{'files':[ref(p) for p in sorted(OUT.iterdir()) if p.is_file()]})
print(json.dumps({'audit':ref(OUT/'audit.final.json'),'proposal':ref(OUT/'scope_proposal.final.json'),
 'handoff':ref(OUT/'handoff.final.json'),'manifest':ref(OUT/'manifest.final.json'),
 'resources':[{k:r[k] for k in ('path','expected_size','expected_sha256','original_commit','git')} for r in resources]},ensure_ascii=False))
