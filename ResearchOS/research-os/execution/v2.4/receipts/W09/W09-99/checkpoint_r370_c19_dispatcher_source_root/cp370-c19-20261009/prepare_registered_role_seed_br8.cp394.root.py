"""Preserve run_id and rebuild the vector from the actual role registration."""
from pathlib import Path
import hashlib,json,os,runpy,sys,uuid
S=Path(__file__).resolve().parent;W=S.parents[1];V=S.parents[4];R=S.parents[6];RUN=W/'w09_br8_actual_root/actual-20261010-01'
def pin(p,rel=False):
    b=p.read_bytes();return dict(path=p.relative_to(R).as_posix() if rel else str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def doc(ref):
    p=Path(ref['path']);p=p if p.is_absolute() else R/p;b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==ref['sha256'] and len(b)==ref['bytes'];return json.loads(b)
regresult=pin(RUN/'publish-registration-c2bc5b2db91547438e6d53a12240012e/result.json');assert regresult['sha256']=='b64f11d6f7da5ee38acd469f23859a7326eaca23753c62c1b7e7a28212dbb160'
reg=doc(regresult);assert pin(V/'checkpoint.json')==reg['checkpoint_ref'] and pin(V/'path_ownership.json')==reg['ownership_ref']
cp=doc(reg['checkpoint_ref']);assert cp['revision']==394
ref3=cp['work_in_progress']['w09_execution_role_registry_ref'];assert set(ref3)=={'path','sha256','bytes'} and ref3['path']=='execution/v2.4/root_delivery_captures/W09/W09-99/execution-roles.json'
roles=doc(ref3); ref2={k:ref3[k] for k in ('path','sha256')}
seed_result=pin(RUN/'seed-c0b41d982ba14201965fe05216e9c82b/result.json');assert seed_result['sha256']=='60f9250bdf24683e51c4663351b45a02728e9d883cc334767b3f6730d9b66291'
context=doc(doc(seed_result)['context_ref']);assert context['run_id']==roles['run_id']=='5e23bbf04e234bff89472bbdbf9653b2'
consumer=pin(RUN/'consume-fb16497eef2f43c2858a3e00df3ba31f/result.json');assert consumer['sha256']=='02ebf5113249e0e0d74ad425be3f78e5898826da95ebe41f21ef86f77d8008f0'
actual=doc(consumer);assert len(actual['processes'])==6 and all(p['actual_exit']==0 and p['observation']['job_cleanup']['handles_closed'] and p['observation']['job_cleanup']['active_processes_last_observed']==0 for p in actual['processes'])
context['registered_commands']=actual['registered_commands'];context['role_policy']=dict(schema='researchos.w09.execution-role-policy.v1',registry_ref=ref3)
context['version_vector']['input_files']=[r for r in context['version_vector']['input_files'] if r['path']!=ref2['path']]+[ref2]
context['global_evidence_refs']={}
sid=uuid.uuid4().hex;inp=RUN/('registered-roles-context-'+sid+'.input.root.json')
with inp.open('xb') as f:f.write((json.dumps(context,ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
extras=RUN/('registered-roles-seed-'+sid+'.extras.root.json')
with extras.open('xb') as f:f.write((json.dumps(dict(context_input_ref=pin(inp)),ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
sys.argv=[str(S/'prepare_br8_actual_stage.root.py'),'prepare','seed',str(extras)]
runpy.run_path(sys.argv[0],run_name='__main__')
