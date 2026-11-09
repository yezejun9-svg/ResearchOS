from pathlib import Path
import ast,copy,hashlib,json,ntpath,re,types
O=Path(__file__).resolve().parent;P=O.parent/'prepare-20261010-01';R=O.parents[6]
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def doc(p):return json.loads(Path(p).read_bytes())
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(O/n)
def check(r):
 a=pin(r['path']);assert a['sha256']==r['sha256'] and a['bytes']==r['bytes'];return r
h=doc(P/'HDF.json');known=doc(P/'known-role-evidence.json')
assert pin(P/'HDF.json')['sha256']=='a093edaea7c228dd114ac1c598a3d0aa18848295882db3996fe78d01e25d56b2'
assert pin(P/'role-registry-input.template.json')['sha256']=='6257cc414141689226bede1078e26ceae3af8471ba59201ae7ea2279774ba5a5'
assert known['Main_ref']['sha256']=='1e04865beef37fdbffa06d649d072721d7b6eb0ef5e525d87bb867da414e4087'
assert known['source_package']['source_ref']['sha256']=='16b9f425efcbe2f7f9155cd7be54c3fe4faf10e327a2800ce6edb89d13fa1668'
guardref=dict(path=str(R/'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'),sha256='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85',bytes=11404)
mode01=known['six_modes'][0]['mode_ref'];mode01=dict(mode01,path=str(R/mode01['path']))
peers={v['role']:v['capture_wrapper_ref'] for v in known['existing_peer_delivery_observations']}
fixed=[pin(P/'HDF.json'),pin(P/'MF.json'),pin(P/'known-role-evidence.json'),h['template_ref'],known['Main_ref'],guardref,
 *known['source_package'].values(),mode01,*peers.values(),*[v['raw_ref'] for v in known['existing_peer_delivery_observations']]]
fixed=list({str(Path(r['path'])).lower():check(r) for r in fixed}.values())
g=types.ModuleType('role_builder_source_guard');g.__file__=guardref['path'];exec(compile(Path(guardref['path']).read_bytes(),guardref['path'],'exec'),g.__dict__)
guard=g.SourceReadGuard();closed=None
try:
 guard.acquire(fixed)
 inputs=dict(schema='researchos.w09-role-input-builder-source-inputs.v1',Main_ref=known['Main_ref'],
  bridge_source_ref=known['source_package']['source_ref'],bridge_hdf_ref=known['source_package']['hdf_ref'],mode01_ref=mode01,
  template_ref=h['template_ref'],peer_audits=peers,guard_ref=guardref,routes=[r['route'] for r in known['six_modes']],fixed_refs=fixed)
 inp=save('source-inputs.json',inputs)
 path=O/'role_input_builder.source.py';raw=path.read_bytes();assert raw.count(b'__SOURCE_INPUTS_SHA__')==1
 path.write_bytes(raw.replace(b'__SOURCE_INPUTS_SHA__',inp['sha256'].encode()))
 candidate=path.read_bytes();tree=ast.parse(candidate)
 names={'need','exact','ref_shape','request_shape','same','unique_refs','audit_payload','allowed_bindings'}
 nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names];assert len(nodes)==len(names)
 assigned={n.targets[0].id:ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('ROLE_ACTORS','ROOT_AUDITS','ROOT_LOG','THREAD')}
 env=dict(Path=Path,ROOT=R,copy=copy,ntpath=ntpath,re=re,**assigned)
 env['REQUEST_FIELDS']={'schema','actor_id','preparation_id','proposal_ref','context_seed_ref',*assigned['ROOT_AUDITS'].values()}
 exec(compile(ast.Module(body=nodes,type_ignores=[]),'<new-pure-metadata-controls-only>','exec'),env)
 mk=lambda name:dict(path=str(O/('synthetic-'+name+'.json')),sha256='a'*64,bytes=1)
 request=dict(schema='researchos.w09-role-input-builder-request.v1',actor_id='codex:/root',preparation_id='0'*32,
  proposal_ref=mk('proposal'),context_seed_ref=mk('context'),**{n:mk(n) for n in assigned['ROOT_AUDITS'].values()})
 checks=[]
 env['request_shape'](request);checks.append(dict(name='exact_request_schema',result='PASS'))
 def reject(name,fn,expected):
  try:fn()
  except ValueError as e:assert str(e)==expected,(name,str(e),expected)
  else:raise AssertionError(name+' accepted')
  checks.append(dict(name=name,rejected_by=expected,result='PASS'))
 reject('missing_dynamic_audit',lambda:env['request_shape'](dict(request,mode01_observation_audit_ref=None)),'EXACT_REF3')
 reject('extra_request_authority',lambda:env['request_shape'](dict(request,execution_grant=True)),'REQUEST_FIELDS')
 reject('nonRoot_request',lambda:env['request_shape'](dict(request,actor_id='/root/full_w09_source_review')),'ROOT_METADATA_REQUEST')
 reject('bool_ref_bytes',lambda:env['ref_shape'](dict(mk('x'),bytes=True)),'TYPED_REF3')
 reject('nonunique_id_shape',lambda:env['request_shape'](dict(request,preparation_id='future')),'FRESH_PREPARATION_ID')
 refs=[mk('raw-source'),mk('raw-executor'),mk('raw-assembler'),mk('raw-verifier'),mk('raw-observer'),mk('assembly-scope')]
 held=env['unique_refs'](refs+[copy.deepcopy(refs[0])]);assert held==refs
 checks.append(dict(name='supplement_six_refs_retained_exact_duplicate_dedup',result='PASS'))
 reject('conflicting_supplement_pin',lambda:env['unique_refs']([refs[0],dict(refs[0],sha256='b'*64)]),'CONFLICTING_PROTECTION_REFS')
 cap=dict(source_line_offsets=[0,1,2],original_line_sha256=['a'*64]*3,source_prefix_size_observed=3)
 before=copy.deepcopy(cap);a=env['audit_payload']('SOURCE_AUTHOR',cap,mk('raw-source'),'a'*64)
 assert set(a)=={'schema','actor_id','role','Root_thread_id','source_audit_path','source_line_offsets','original_line_sha256','source_prefix_size_observed','original_capture_ref','binding_sha256'}
 assert a['actor_id']=='/root/full_w09_source_review' and a['source_audit_path']==assigned['ROOT_LOG'] and cap==before
 checks.append(dict(name='eleven_field_adapter_backend_actor_preserves_original_metadata',result='PASS'))
 allowed=env['allowed_bindings'](dict(sha256='a'*64),dict(source_hdf_ref=dict(sha256='b'*64),report_sha256='c'*64,unrelated_ref=dict(sha256='d'*64)))
 assert allowed=={'a'*64,'b'*64,'c'*64};checks.append(dict(name='binding_allowlist_excludes_unrelated_hash',result='PASS'))
 imports=[n.names[0].name for n in tree.body if isinstance(n,ast.Import)]
 assert not any(x in ('sqlite3','subprocess') for x in imports)
 save('pure-metadata-controls.json',dict(schema='researchos.w09-role-builder-pure-metadata-controls.v1',count=len(checks),checks=checks,
  synthetic_metadata_only=True,actual_audit_verification_or_helper_run=False,Root_stage_Native_SQL_models_TP_calls=0,old_controls_replayed=False))
 template={k:(request[k] if k in ('schema','actor_id') else None) for k in request}
 save('builder-request.template.json',template)
 save('source-decision.json',dict(status='SOURCE_ONLY_PENDING_ROOT_REVIEW',source_ref=pin(path),source_inputs_ref=inp,
  prior_template_hdf_ref=pin(P/'HDF.json'),new_pure_metadata_controls=len(checks),Root_builder_run=False,
  future_origin_copies_issued=False,Main_Canon_Scope_fixed_registry_writes=0,Root_stage_Native_SQL_models_TP_calls=0,
  formal_acceptance=False,execution_grant=False,self_acceptance=False))
 save('protected-inputs.json',fixed)
 assert all(check(r) for r in fixed)
finally:
 closed=guard.close();save('SourceGuard.closed.json',closed)
assert closed['closed'] and closed['retained_handles_count']==0 and not closed['errors']
print(json.dumps(dict(status='SOURCE_PREPARED_UNSEALED',source_ref=pin(O/'role_input_builder.source.py'),controls_ref=pin(O/'pure-metadata-controls.json'),source_guard_closed_zero=True),ensure_ascii=False))
