import difflib,hashlib,json,pathlib
E=pathlib.Path(__file__).parent
A=pathlib.Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/desktop_main7d_native_codex/20261025-current-chat/complete-tree')
W=pathlib.Path('D:/作品集/ResearchOS/research-os/.local/worktrees/desktop-main7d-native-20261025')
def sha(data):return hashlib.sha256(data).hexdigest()
freeze=(A/'SOURCE-FREEZE-03.json').read_bytes();patch=(A/'SOURCE-FREEZE-03.patch').read_bytes()
assert sha(freeze)=='c6ac8745f27d91a7d74aa804acdc05f3a50932b0d414a91f63daefe75c00c113'
assert sha(patch)=='7da9b434521f14857766b4d502738fbdff0aadcb1e780228b26d0020c85213d4'
f=json.loads(freeze);r2=json.loads((E/'r2-fixed-inputs/source-freeze-02.json').read_bytes())
assert f['base_commit']==r2['base_commit'] and f['base_tree']==r2['base_tree'] and f['candidate_delta']==r2['candidate_delta']
changed=[p for p,r in f['seven_file_hashes'].items() if r!=r2['seven_file_hashes'][p]]
assert sorted(changed)==['apps/desktop/launch-development.mjs','tests/ui/desktop/development-launcher.test.mjs']
S=E/'source-r3';S.mkdir(exist_ok=False)
fixed=E/'r3-fixed-inputs';fixed.mkdir(exist_ok=False)
(fixed/'SOURCE-FREEZE-03.json').write_bytes(freeze);(fixed/'SOURCE-FREEZE-03.patch').write_bytes(patch)
diff=[]
for name,row in f['seven_file_hashes'].items():
    data=(W/name).read_bytes();assert sha(data)==row['sha256'] and len(data)==row['bytes']
    target=S/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    assert data==(W/name).read_bytes()
    if name in changed:diff.extend(difflib.unified_diff((E/'source-r2'/name).read_text(encoding='utf-8').splitlines(True),data.decode('utf-8').splitlines(True),fromfile='r2/'+name,tofile='r3/'+name))
delta=''.join(diff)
(E/'R3-two-file-delta.diff').write_text(delta,encoding='utf-8',newline='\n')
result={'source_freeze_sha256':sha(freeze),'patch_sha256':sha(patch),'source_digest':f['source_snapshot_digest'],'changed_since_r2':changed,'seven':f['seven_file_hashes'],'delta_sha256':sha((E/'R3-two-file-delta.diff').read_bytes())}
(E/'R3-independent-snapshot-manifest.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result));print(delta)
