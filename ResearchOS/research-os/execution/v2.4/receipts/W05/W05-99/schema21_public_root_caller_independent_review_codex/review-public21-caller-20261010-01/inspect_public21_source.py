from pathlib import Path
import ast,datetime,hashlib,json,sys,types
R=Path(r'D:/作品集/ResearchOS/research-os');D=Path(__file__).resolve().parent
B=R/'execution/v2.4/receipts/W05/W05-99';N=B/'schema21_public_root_caller_source_codex/s21public-caller-20261010-01'
S=R/'execution/v2.4/receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
G=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
GREF={'path':str(G),'sha256':'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85','bytes':11404}
AUTHOR='codex:/root/backup_regression_resources';REVIEWER='codex:/root/full_w09_source_review'
THREAD='01a1215b-7210-7613-b033-756b9d553b83'

def pin(path):
    path=Path(path);raw=path.read_bytes();return {'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def write(name,value):
    path=D/name
    with path.open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
    return pin(path)
def inert(path,raw=None):
    path=Path(path);module=types.ModuleType(path.stem);module.__file__=str(path)
    exec(compile(path.read_bytes() if raw is None else raw,str(path),'exec'),module.__dict__);return module
def exact(path,sha,size):return dict(path=str(path),sha256=sha,bytes=size)
def shape(value):
    if type(value) is dict:return {'type':'dict','keys':list(value),'scalars':{k:v for k,v in value.items() if v is None or type(v) in (str,int,bool,float)}}
    if type(value) is list:return {'type':'list','length':len(value),'first_two':[shape(x) for x in value[:2]]}
    return {'type':type(value).__name__,'value':value}

def main():
    fixed=[exact(N/'HDF.json','d9504dc664f2e5257ae9355de381827f65b57eca9d03c7c8ebe63f7fe37e763a',8556),exact(N/'MF.json','3d1ed3b57cd46d109164ad6fb2ecf37c9949de23717883feb3256bf8a7858dfd',90265),exact(N/'public21_root.source.py','010b3907632f6e065b9765b880fd57287950e5464d6410415484f8121111bd63',55236),exact(N/'root-calling-contract.source.json','84970856d1982fcfa8b1fe56343b6a0af62bc46d787894ea423d855e7dbfd543',23301),exact(S/'w09.public21-root-caller-source.actual-audit.root.json','1b411c3d56d9d1b25fe7ab0fb42a672d981f9d0bd9be0d5062ea31011de3ae24',1122)]
    for ref in fixed:assert pin(ref['path'])==ref
    manifest=json.loads(Path(fixed[1]['path']).read_bytes());handoff=json.loads(Path(fixed[0]['path']).read_bytes())
    refs=fixed+manifest['members']+[handoff['OC3_source_ref'],*handoff['runner_source_refs'].values(),*handoff['actual_accepted_runner_review_refs'].values(),handoff['old21_programme_ref'],handoff['real_existing_runner_peer_audit_ref']]
    author_audit=json.loads(Path(fixed[4]['path']).read_bytes());refs.append(author_audit['original_capture_ref'])
    inputs=json.loads(Path(handoff['source_inputs_ref']['path']).read_bytes())
    # Inspect only the actual Source input inventory; no recursive historic Canon traversal.
    input_shapes={k:shape(v) for k,v in inputs.items()}
    if type(inputs.get('references')) is list:refs+=inputs['references']
    unique={str(Path(ref['path'])):{**ref,'path':str(Path(ref['path']))} for ref in refs}
    forbidden={str(R/'execution/v2.4'/name) for name in ('checkpoint.json','path_ownership.json','step_state.json','commands.json')}
    assert not any(path in forbidden for path in unique)
    assert pin(G)==GREF;guard_module=inert(G);guard=guard_module.SourceReadGuard(per_file_cap=512*1024*1024,total_cap=2*1024*1024*1024)
    try:
        guard.acquire(list(unique.values()));get=lambda path:guard.get_buffer(str(path))
        caller=inert(N/'public21_root.source.py',get(N/'public21_root.source.py'))
        caller._base=inert(handoff['OC3_source_ref']['path'],get(handoff['OC3_source_ref']['path']))
        contracts={'caller':json.loads(get(N/'root-calling-contract.source.json')),'runner':json.loads(get(handoff['runner_source_refs']['contract_ref']['path']))}
        closures={'caller_manifest_members':len(manifest['members']),'caller_manifest_member_bytes':sum(ref['bytes'] for ref in manifest['members']),'held_ref_count':len(unique),'held_bytes':sum(ref['bytes'] for ref in unique.values()),'Source_input_field_shapes':input_shapes}
        code=get(N/'public21_root.source.py').decode();tree=ast.parse(code)
        functions={node.name:{'line':node.lineno,'end_line':node.end_lineno,'source':ast.get_source_segment(code,node)} for node in tree.body if isinstance(node,(ast.FunctionDef,ast.ClassDef))}
        raw=get(author_audit['original_capture_ref']['path']);rows=[json.loads(line) for line in raw.splitlines()];assert len(rows)==3
        with Path(author_audit['source_audit_path']).open('rb') as f:
            for offset,line in zip(author_audit['source_line_offsets'],raw.splitlines(keepends=True)):
                f.seek(offset);assert f.read(len(line))==line
        header,meta,final=rows;payload=final['payload'];text=payload['content'][0]['text']
        try:delivery_shape=shape(caller.decode_peer_body(text,AUTHOR))
        except (ValueError,RuntimeError):delivery_shape={'type':'Source-author prose or alternate delivery; not a Root review grant'}
        capture_checks={'raw_sha_bytes_pin':True,'original_source_offsets_readback':True,'Root_header_thread':header['payload']['id']=='01a11007-5233-7ca1-b71f-9e9e5ce84c98','actual_Backup_author':payload.get('author')==AUTHOR.removeprefix('codex:'),'recipient_Root':payload.get('recipient')=='/root','client_authored_false':final.get('metadata',{}).get('client_authored') is False,'adjacent_ordinals':final['ordinal']==meta['ordinal']+1,'time_delta_seconds':(caller.when(final['timestamp'])-caller.when(meta['timestamp'])).total_seconds(),'line_sha256_matches':[hashlib.sha256(line).hexdigest() for line in raw.splitlines(keepends=True)]==author_audit['original_line_sha256'],'complete_Source_HDF_SHA_in_final':handoff['manifest_ref']['sha256'] in text and fixed[0]['sha256'] in text,'delivery_shape':delivery_shape}
        observations={'schema':'researchos.public21-caller-independent-source-observations.v1','review_author':REVIEWER,'review_thread_id':THREAD,'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_hdf_ref':fixed[0],'source_mf_ref':fixed[1],'caller_ref':fixed[2],'calling_contract_ref':fixed[3],'Root_actual_author_audit_ref':fixed[4],'source_manifest':manifest,'source_handoff':handoff,'source_inputs':inputs,'contracts':contracts,'source_functions':functions,'root_source_author_capture_checks':capture_checks,'closures':closures,'held_refs':list(unique.values()),'actual_product_calls':0,'RootScope_or_qualification_issued':False,'live_Canon_read_or_held':False,'author58_controls_rerun':False,'execution_grant':False,'formal_acceptance':False}
        ref=write('source-observations.json',observations)
    finally:
        closed=guard.close();guard_ref=write('source-inspection.guard.closed.json',closed)
        assert closed['closed'] is True and closed['retained_handles_count']==0 and not closed['errors']
    print(json.dumps({'observation_ref':ref,'guard_ref':guard_ref,'closures':closures,'actual_author_checks':capture_checks,'contract_keys':{k:list(v) for k,v in contracts.items()},'all_guards_closed':True,'retained_handles_count':0,'product_calls':0},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
