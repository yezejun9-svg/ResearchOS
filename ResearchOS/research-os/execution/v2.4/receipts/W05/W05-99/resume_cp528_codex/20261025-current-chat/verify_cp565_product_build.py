"""Bind the ASAR repair and build05 without launching the product."""
import datetime,hashlib,json
from pathlib import Path
from preserve_main_baseline import R,N,git,read,ref
from preserve_desktop_main_ecc28 import verify

def checked(row,base):
    p=Path(row['path']);p=p if p.is_absolute() else base/p
    assert p.is_file() and not p.is_symlink() and not(getattr(p.stat(),'st_file_attributes',0)&0x400),str(p)
    actual=ref(p);assert actual['sha256']==row['sha256'] and actual['bytes']==row['bytes'],str(p)
    return actual

def main():
    preserved=verify();W=R/'.local/worktrees/desktop-installed-delivery-20261025'
    E=R/'execution/v2.4/receipts/W05/W05-99/installed_delivery_codex/20261025-current-chat/continuation-20261028/asar-repair-cp565'
    commit='5c4c94022bd92da68ef544f2779527bfe065c428';tree='133c6fdee17e1ad2f7758689c55c1486e778cec0'
    assert git(W,'rev-parse','HEAD').decode().strip()==commit and git(W,'rev-parse','HEAD^{tree}').decode().strip()==tree
    assert git(W,'rev-parse','HEAD^').decode().strip()=='448af57c208a3f29199d10e0fa9d9c7311776fad'
    assert not git(W,'status','--porcelain=v1','--untracked-files=all')
    scope=read(N/'continuation-cp565/ASAR-exact2-repair-scope.json')
    changed=git(W,'diff','--name-only','HEAD^','HEAD').decode().splitlines()
    assert set(changed)==set(scope['allowed_source_paths'])
    checked(scope['unchanged_loader_ref'],W)
    B=E/'build-05';result=read(B/'result.json');bundle=Path(result['output'])
    assert result['source_drift'] is False and result['input_drift'] is False
    marker=read(bundle/'installed-product.json')
    assert ref(bundle/'installed-product.json')['sha256']==result['manifest_sha256']
    assert (bundle/'installed-product.json').read_bytes()==(B/'installed-product.json').read_bytes()
    assert marker['source_commit']==commit and marker['install_root']==str(bundle) and marker['installation_id']==result['installation_id']
    inputs=[]
    for name in ['source','go-compiled-inputs','mu-compiled-inputs','mu-vendor-5083','public-mu']:
        a,b=B/(name+'.before.json'),B/(name+'.after.json');assert a.read_bytes()==b.read_bytes(),name
        inputs.extend([ref(a),ref(b)])
    source=read(B/'source.before.json');assert source['head']==commit and source['tree']==tree and source['candidate_delta']==[]
    source_refs=[checked(row,W) for row in source['files']]
    inventory=marker['files'];names=[row['path'] for row in inventory]
    assert names==sorted(names) and len({n.lower() for n in names})==len(names)==133
    observed=[]
    for p in bundle.rglob('*'):
        assert not p.is_symlink() and not(getattr(p.stat(),'st_file_attributes',0)&0x400),str(p)
        if p.is_file():observed.append(p.relative_to(bundle).as_posix())
    assert set(observed)==set(names)|{'installed-product.json'}
    outputs=[checked(row,bundle) for row in inventory]
    iv='researchos.product-inventory/1\n'+''.join(f"{r['path']}\n{r['sha256']}\n{r['bytes']}\n" for r in inventory)
    assert hashlib.sha256(iv.encode()).hexdigest()==marker['inventory_digest']
    values=[marker['schema'],str(bundle),commit,marker['source_digest'],marker['inventory_digest'],marker['product_version'],marker['client_protocol'],str(marker['schema_version'])]
    values += [marker['binaries'][key]['sha256'] for key in ['cli','control','electron','verifier','validator']]
    assert hashlib.sha256(('\n'.join(values)+'\n').encode()).hexdigest()==marker['installation_id']
    v=read(bundle/'apps/desktop/resources/control/runtime-verifier-installation.json')
    assert v['executable']==str(bundle/marker['binaries']['verifier']['path'])
    assert v['executable_hash']=='sha256:'+marker['binaries']['verifier']['sha256'] and v['arguments']==[] and v['source_commit']==commit
    probe=json.loads((E/'probe-stdout.raw').read_text(encoding='utf-8-sig').strip())
    assert probe['patched']=={'file':False,'directory':True} and probe['default_loader']['code']=='PRODUCT_PATH_TYPE'
    assert probe['physical']['file'] and not probe['physical']['directory'] and probe['physical_loader']['ok'] and probe['physical_loader']['file_count']==133
    report={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'ROOT_ASAR_SOURCE_BUILD_BINDING_VERIFIED_NOT_NATIVE_ACCEPTANCE','commit':commit,'tree':tree,'exact_changed_paths':changed,'preserved':preserved,
        'build_result':ref(B/'result.json'),'marker':ref(bundle/'installed-product.json'),'source_refs':source_refs,'output_refs':outputs,'before_after_inputs':inputs,
        'probe_refs':[ref(E/n) for n in ['probe-stdout.raw','probe-stderr.raw','probe-exit.json','probe-pid.json','probe-invocation.json']],
        'native_product_runs':0,'formal_increment':0,'dependency_scope':'Full before/after manifests compared; independent reviewer rehashes compiled closure.'}
    output=N/'continuation-cp565/product-host-build05-root-verification.json'
    with output.open('x',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'status':report['status'],'source_files':len(source_refs),'inventory_files':len(outputs),'ref':ref(output)}))

if __name__=='__main__':main()
