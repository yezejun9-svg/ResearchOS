"""Root read-only binding of the frozen product host and final build."""
import datetime, hashlib, json
from pathlib import Path
from preserve_main_baseline import R, N, git, read, ref
from preserve_desktop_main_ecc28 import verify

W=R/'.local/worktrees/desktop-installed-delivery-20261025'
E=R/'execution/v2.4/receipts/W05/W05-99/installed_delivery_codex/20261025-current-chat/continuation-20261028'
COMMIT='5ee2c694ee275a72f40e8aa1d6c377d719fb8631'
TREE='43e71226bbcb5d413bfa0ca2b11a767d255b2aec'

def check(row, base):
    p=Path(row['path'])
    if not p.is_absolute():p=base/p
    assert p.is_file() and not p.is_symlink(),str(p)
    actual=ref(p)
    assert actual['sha256']==row['sha256'] and actual['bytes']==row['bytes'],str(p)
    return actual

def main():
    preserved=verify()
    assert git(W,'rev-parse','HEAD').decode().strip()==COMMIT
    assert git(W,'rev-parse','HEAD^{tree}').decode().strip()==TREE
    assert git(W,'rev-parse','HEAD^').decode().strip()=='ecc28dd3c91a0f68dcddb41b53325aa7f0e81419'
    assert not git(W,'status','--porcelain=v1','--untracked-files=all')
    scope=read(N/'continuation-cp558/Product-host-exact14-source-scope.json')
    changed=git(W,'diff','--name-only','HEAD^','HEAD').decode().splitlines()
    assert set(changed)==set(scope['allowed_source_paths']) and len(changed)==14
    B=E/'build-02';result=read(B/'result.json');bundle=Path(result['output'])
    marker=read(bundle/'installed-product.json')
    assert ref(bundle/'installed-product.json')['sha256']==result['manifest_sha256']=='7c04fc8d33b30382027fded7120265cf6cef61bd9785fe0c3cf02e15acf29144'
    assert (bundle/'installed-product.json').read_bytes()==(B/'installed-product.json').read_bytes()
    assert marker['source_commit']==COMMIT and marker['install_root']==str(bundle)
    assert marker['installation_id']==result['installation_id']=='318a306090d0fd24573e38b23bdea775435dc26696f43766cf7dd2225b1d2bb2'
    inputs=[]
    for name in ['source','go-compiled-inputs','mu-compiled-inputs','mu-vendor-5083','public-mu']:
        a,b=B/(name+'.before.json'),B/(name+'.after.json')
        assert a.read_bytes()==b.read_bytes(),name
        inputs.extend([ref(a),ref(b)])
    source=read(B/'source.before.json')
    assert source['head']==COMMIT and source['tree']==TREE and source['candidate_delta']==[]
    source_refs=[check(row,W) for row in source['files']]
    inventory=marker['files'];names=[row['path'] for row in inventory]
    assert names==sorted(names) and len({x.lower() for x in names})==len(names)==133
    observed=[]
    for p in bundle.rglob('*'):
        assert not p.is_symlink() and not (getattr(p.stat(),'st_file_attributes',0)&0x400),str(p)
        if p.is_file():observed.append(p.relative_to(bundle).as_posix())
    assert set(observed)==set(names)|{'installed-product.json'}
    output_refs=[check(row,bundle) for row in inventory]
    iv='researchos.product-inventory/1\n'+''.join(f"{row['path']}\n{row['sha256']}\n{row['bytes']}\n" for row in inventory)
    assert hashlib.sha256(iv.encode()).hexdigest()==marker['inventory_digest']
    values=[marker['schema'],str(bundle),COMMIT,marker['source_digest'],marker['inventory_digest'],marker['product_version'],marker['client_protocol'],str(marker['schema_version'])]
    values += [marker['binaries'][key]['sha256'] for key in ['cli','control','electron','verifier','validator']]
    assert hashlib.sha256(('\n'.join(values)+'\n').encode()).hexdigest()==marker['installation_id']
    v=read(bundle/'apps/desktop/resources/control/runtime-verifier-installation.json')
    assert v['executable']==str(bundle/marker['binaries']['verifier']['path'])
    assert v['executable_hash']=='sha256:'+marker['binaries']['verifier']['sha256'] and v['arguments']==[] and v['source_commit']==COMMIT
    report={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'ROOT_FROZEN_SOURCE_BUILD_BINDING_VERIFIED_NOT_NATIVE_ACCEPTANCE',
        'commit':COMMIT,'tree':TREE,'source_files':len(source_refs),'inventory_files':len(output_refs),'exact_changed_paths':changed,
        'preserved':preserved,'build_result':ref(B/'result.json'),'marker':ref(bundle/'installed-product.json'),
        'source_refs':source_refs,'output_refs':output_refs,'before_after_inputs':inputs,
        'dependency_scope':'Root compares full before/after manifests; independent reviewer separately rehashes Go/Mu/vendor closure',
        'native_runs':0,'formal_increment':0,'remaining':'ModelStream exact7 and independent final review; actual native lifecycle; installers and full formal goal'}
    p=N/'continuation-cp561/product-host-final-build-root-verification.json'
    with p.open('x',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'status':report['status'],'source_files':len(source_refs),'inventory_files':len(output_refs),'evidence_sha256':ref(p)['sha256']}))

if __name__=='__main__':main()
