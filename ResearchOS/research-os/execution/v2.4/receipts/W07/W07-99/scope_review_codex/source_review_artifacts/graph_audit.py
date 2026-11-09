import hashlib,json,pathlib,sqlite3
ROOT=pathlib.Path(__file__).resolve().parents[7]
CAND=ROOT/'.local/worktrees/codex-w0799'
RUN=CAND/'execution/v2.4/receipts/W07/W07-99/source_executor_codex/run-e24ecdbc16ae48d5b7805b8e6fa26e16'
OUT=pathlib.Path(__file__).parent
def sha(b):return 'sha256:'+hashlib.sha256(b).hexdigest()
def canonical(o):return json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def obj(db,project,kind,id,revision=None):
 q='SELECT body FROM '+('domain_versions' if revision else 'domain_objects')+' WHERE project=? AND kind=? AND id=?';args=[project,kind,id]
 if revision:q+=' AND revision=?';args.append(revision)
 row=db.execute(q,args).fetchone();assert row,(kind,id,revision);return json.loads(row[0])
def deref(db,project,r):
 o=obj(db,project,r['entity_type'],r['id'],r['revision']);assert o['revision']==r['revision'];assert o.get('content_hash',o.get('receipt_hash'))==r['content_hash'];return o
def body(db,a):
 row=db.execute('SELECT bytes,content_hash,sealed FROM uploaded_content WHERE project=? AND storage_key=?',(a['project_id'],a['storage_key'])).fetchone();assert row and row[2]==1;assert sha(row[0])==row[1]==a['content_hash'];assert len(row[0])==a['byte_size'];return row[0]
def health(db,project,r):
 a=deref(db,project,r);assert a['kind']=='REPORT' and a['validity']=='CURRENT' and a['evidence_kind']=='GENERATED';d=json.loads(body(db,a));assert d['schema']=='researchos.source-health.v1';assert a['input_refs']==[d['cursor_ref'],d['profile_ref']];assert a['source_refs']==d['source_refs'];cursor=deref(db,project,d['cursor_ref']);profile=deref(db,project,d['profile_ref']);configs=[c for c in profile['source_configs'] if c['source_id']==d['source_id']];assert len(configs)==1;assert sha(canonical(configs[0]))==d['config_hash'];assert sha(canonical(d['query']))==d['query_hash']==cursor['query_hash'];
 for r in a['source_refs']:
  o=deref(db,project,r)
  if r['entity_type']=='Artifact':body(db,o)
  if r['entity_type']=='Evidence':body(db,deref(db,project,o['snapshot_artifact_ref']))
 return d
result={'scope':'Independent bounded read-only SQLite graph verification; proves sealed bytes/relations, not trusted ingress safety','live':[],'h07':[]}
for kind in ['GITHUB','PAPER','X']:
 report=json.loads((RUN/f'report-{kind}.json').read_bytes());path=RUN/f'live-{kind}.sqlite';before=sha(path.read_bytes());db=sqlite3.connect(path.resolve().as_uri()+'?mode=ro&immutable=1',uri=True);assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok';project=report['project_id'];h=health(db,project,report['health_artifact_ref']);assert h['health']==report['health'];assert h['health']['requested_from']==report['window_from'] and h['health']['requested_to']==report['window_to'];assert h['source_id']==report['source_id'];manifest=obj(db,project,'Artifact',report['manifest']['artifact_id']);m=json.loads(body(db,manifest));assert manifest['content_hash']==report['manifest']['sha256'];assert m['source_id']==report['source_id'];raw=obj(db,project,'Artifact',report['raw_page']['artifact_id']);assert sha(body(db,raw))==report['raw_page']['sha256'];assert m['raw_artifact_ref']['id']==raw['id'];assert len(m['evidence_refs'])==len(report['items'])>=1
 for item in report['items']:
  e=obj(db,project,'Evidence',item['evidence_id']);a=deref(db,project,e['snapshot_artifact_ref']);b=body(db,a);assert sha(b)==item['body_sha256'] and len(b)==item['body_bytes'];assert e['canonical_url']==item['url'] and e['publisher']==item['author'] and e['published_at']==item['published_at'] and e['retrieved_at']==item['retrieved_at'] and e['upstream_revision']==item['upstream_revision'];assert item['artifact_ref']==e['snapshot_artifact_ref'];assert any(r['id']==e['id'] for r in m['evidence_refs']);assert any(meta['upstream_id']==item['upstream_id'] and meta['body_sha256']==sha(b) for meta in m['item_metadata'])
 cursor=obj(db,project,'SourceCursor',report['cursor_id']);row={'kind':kind,'db_sha256':before,'items':len(report['items']),'health':report['health'],'cursor_covered_until':cursor['covered_until'],'cursor_opaque':cursor['opaque_cursor'],'raw_body_manifest_health_graph':'PASS'}
 if kind=='X':
  assert cursor['covered_until'] is None and cursor['opaque_cursor'] is None and not report.get('next_cursor') and not report['page_complete'];claim=report['claim_check'];a=deref(db,project,claim['artifact_ref']);doc=json.loads(body(db,a));assert doc=={k:v for k,v in claim.items() if k!='artifact_ref'};e=deref(db,project,doc['x_evidence_ref']);assert e['source_kind']=='X' and e['stance']=='CONTEXT' and e['verification_status']=='UNVERIFIED';assert doc['x_snapshot_ref']==e['snapshot_artifact_ref'];body(db,deref(db,project,doc['x_snapshot_ref']));assert doc['adoption_authority'] is False and doc['conclusion']=='NOT_CORROBORATED' and doc['primary_evidence_ref'] is None;row['selected_claim_graph']='NOT_CORROBORATED; exact selected evidence/snapshot sealed; no adoption authority'
 db.close();assert sha(path.read_bytes())==before;result['live'].append(row)
for row in json.loads((RUN/'h07-assertions.json').read_bytes()):
 path=pathlib.Path(row['db_snapshot_path']);assert path.resolve().is_relative_to(RUN.resolve());before=sha(path.read_bytes());db=sqlite3.connect(path.resolve().as_uri()+'?mode=ro&immutable=1',uri=True);project=row['project_id'];actual=row['actual'];check={'id':row['id'],'mode':row['measurement_mode'],'db_sha256':before};assert row['measurement_mode']=='INJECTED'
 if 'health_artifact_ref' in actual:
  d=health(db,project,actual['health_artifact_ref']);assert d['health']==actual['health'];check['health_status']=d['health']['status'];check['reason']=d['health']['reason'];cursor=obj(db,project,'SourceCursor',actual['cursor']['id']);assert cursor==actual['cursor'] and cursor['covered_until'] is None;check['evidence_count']=len(actual['evidence'] or []);check['page_complete']=actual['page_complete'];check['source_pages']=db.execute('SELECT count(*) FROM source_pages WHERE project=?',(project,)).fetchone()[0]
  if actual['manifest']:
   m=obj(db,project,'Artifact',actual['manifest']['id']);assert m==actual['manifest'];md=json.loads(body(db,m));check['pr_states']=[x['pr_state'] for x in md['item_metadata']]
 if 'cycle' in actual:
  c=obj(db,project,'ResearchCycle',actual['cycle']['id']);assert c==actual['cycle'] and c['status']=='PARTIAL';check['cycle_status']=c['status'];check['source_coverage']=c['source_coverage']
 if 'effect' in actual:
  e=actual['effect'];stored=json.loads(db.execute('SELECT body FROM resource_effects WHERE project=? AND run=? AND effect_key=? ORDER BY sequence DESC LIMIT 1',(project,e['run_id'],e['key'])).fetchone()[0]);assert stored==e;check['effect_state']=e['state'];assert e['state']==('CONFIRMED' if row['id']=='effect_confirmed' else 'UNKNOWN')
 db.close();assert sha(path.read_bytes())==before;result['h07'].append(check)
(OUT/'sealed_graph_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'live':len(result['live']),'h07':len(result['h07']),'graph_audit_sha256':sha((OUT/'sealed_graph_audit.json').read_bytes())}))
