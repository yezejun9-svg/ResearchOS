"""Root future pure-metadata binding builder. No implicit live tuple or resource selection.
Only emits a new immutable binding; does not execute another template or grant.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT=Path('D:/作品集/ResearchOS/research-os')
V3_GATE_SHA='7933e679bbda76df1aca4f21119d34a5b18791343d4b442481e19ed1df0c85b1'

def need(v,m):
    if not v: raise RuntimeError(m)

def strict(b):
    def pairs(items):
        d={}
        for k,v in items:
            need(k not in d,'duplicate key'); d[k]=v
        return d
    return json.loads(b.decode('utf-8',errors='strict'),object_pairs_hook=pairs,
        parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))

def safe(value,exists=True):
    p=Path(value); p=p if p.is_absolute() else ROOT/p
    need(p.is_relative_to(ROOT) and p!=ROOT and '..' not in p.parts and p.resolve(strict=exists)==p.absolute(),'bounded path')
    for q in [p,*p.parents]:
        if os.path.lexists(q): need(not q.is_symlink() and not(getattr(q.lstat(),'st_file_attributes',0)&0x400),'alias')
        if q==ROOT:break
    return p

def pinned(value):
    r=strict(value.encode('utf-8')); need(isinstance(r,dict) and set(r)=={'path','sha256','bytes'},'exact JSON ref')
    p=Path(r['path']); p=p if p.is_absolute() else ROOT/p
    if p.is_relative_to(ROOT): p=safe(p)
    raw=p.read_bytes(); need(len(raw)==r['bytes'] and hashlib.sha256(raw).hexdigest()==r['sha256'],'ref bytes')
    return r

def main():
    need(sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode,'-I -S -X utf8')
    ap=argparse.ArgumentParser()
    for name in ('scope-template-ref','runtime-resources-ref','compiler-resources-ref','current43-authority-ref',
                 'origin-cut-ref','canonical-before-ref','source-inputs-ref','metadata-code-refs-ref','failure-prefix430-ref'):
        ap.add_argument('--'+name,required=True,type=pinned)
    ap.add_argument('--controller-review-ref',required=True,help='Exact ref JSON, or literal null only for pre-review scope stage')
    for name in ('before','after','main-git','public-environment'):
        ap.add_argument('--'+name,required=True,type=lambda x:strict(x.encode('utf-8')))
    for name in ('run-uuid','registration-namespace','controller-review-path','new-output-root','new-wrapper-root',
                 'new-export-root','new-authorization-root','output'):
        ap.add_argument('--'+name,required=True)
    a=ap.parse_args(); s=strict(safe(a.scope_template_ref['path']).read_bytes())
    need(s['authorization_gate_ref']['sha256']==V3_GATE_SHA,'new v3 scope template required')
    need(s['preparation_only'] is True and s['execution_authorized'] is False,'template provenance')
    for t in (a.before,a.after):need(isinstance(t,list) and len(t)==3 and all(type(x)is int for x in t),'explicit tuple')
    need(a.before[0]>323 and a.before[2]>=430 and a.after[:2]==[a.before[0]+1,a.before[1]+1] and a.after[2]>=a.before[2],'forward tuple')
    need(a.main_git['head']==s['source_commit'] and a.main_git['status_rows']==13 and a.main_git['deleted_rows']==11
         and a.main_git['index_empty'] is True and len(a.main_git['status_sha256'])==64
         and type(a.main_git['status_bytes'])is int,'explicit actual Main43 guard')
    need(len(a.run_uuid)==32 and all(c in '0123456789abcdef' for c in a.run_uuid),'UUID')
    roots=[safe(getattr(a,n),False) for n in ('new_output_root','new_wrapper_root','new_export_root','new_authorization_root')]
    need(len(set(roots))==4 and all(a.run_uuid in p.name and not p.exists() for p in roots),'new disjoint leaves')
    need(all(not x.is_relative_to(y) for x in roots for y in roots if x!=y),'overlap')
    ns=safe(a.registration_namespace); need(ns.is_relative_to(ROOT/'execution/v2.4/receipts/W05/W05-99/integration_codex'),'Root namespace')
    dest=safe(a.output,False); need(dest.parent==ns,'binding output location')
    code=strict(safe(a.metadata_code_refs_ref['path']).read_bytes())['entries']
    for r in code:pinned(json.dumps(r))
    rreview=None if a.controller_review_ref=='null' else pinned(a.controller_review_ref)
    if rreview:need(safe(rreview['path'])==safe(a.controller_review_path),'review path')
    b={k:s[k] for k in ('runner_ref','launcher_ref','authorization_gate_ref','owned_process_helper_ref',
        'debug_tree_helper_ref','toolchain_lock_ref','python_flags')}
    b.update(schema='researchos.cli43-root-metadata-binding.v1',owner='codex:/root',preparation_only=False,
        execution_authorized=True,before=a.before,after=a.after,main_git=a.main_git,public_environment=a.public_environment,
        run_uuid=a.run_uuid,registration_namespace=ns.relative_to(ROOT).as_posix(),
        controller_review_path=str(safe(a.controller_review_path,False)),controller_review_ref=rreview,
        registration_metadata_paths=['execution/v2.4/checkpoint.json','execution/v2.4/path_ownership.json'],
        metadata_code_refs=code,formal_increment=0)
    for name in ('runtime_resources_ref','compiler_resources_ref','current43_authority_ref','origin_cut_ref',
                 'canonical_before_ref','source_inputs_ref','failure_prefix430_ref','new_output_root','new_wrapper_root','new_export_root','new_authorization_root'):
        b[name]=getattr(a,name)
    # A binding is configuration for reviewed metadata scripts, not a runtime grant.
    b['authority_semantics']='DRAFT_CONFIGURATION_ONLY; actual sealed CAS and grant still mandatory'
    with dest.open('xb') as f:f.write((json.dumps(b,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8'))

if __name__=='__main__':
    try:main()
    except BaseException as e:
        sys.stderr.write(json.dumps({'stage':'BUILD_BINDING','error':repr(e),'actual_native_exit':None,
            'automatic_retry':False,'counter_reset':False},ensure_ascii=False)+'\n')
        raise SystemExit(1)
