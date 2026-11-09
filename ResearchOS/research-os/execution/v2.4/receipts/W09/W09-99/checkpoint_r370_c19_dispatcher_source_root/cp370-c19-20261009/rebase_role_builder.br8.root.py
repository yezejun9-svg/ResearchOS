"""Prepare a constants-only BR8 metadata helper; do not run its builder."""
from pathlib import Path
import ast, hashlib, json, os
S=Path(__file__).resolve().parent; W=S.parents[1]
OLD=W/'w09_br7_role_input_preparation_codex/prepare-20261010-02'
NEW=W/'w09_br8_role_input_preparation_root/prepare-20261010-01'
SRC=W/'w09_formal_root_bridge_source_codex/bridge-20261010-08'
def pin(p):
    raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(p,raw):
    with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    return pin(p)
def encoded(v):return (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode()
oldsource=(OLD/'role_input_builder.source.py').read_bytes();oldinputs=(OLD/'source-inputs.json').read_bytes()
assert hashlib.sha256(oldsource).hexdigest()=='15425e193fdec56e49048e5788f6d59b6dab8fbb410d071fa083d07ab95046a5'
assert hashlib.sha256(oldinputs).hexdigest()=='50930e0d982b5c7c570280cf2f9e65ad273256176ea3eaf637763e8926244c12'
i=json.loads(oldinputs);before=dict(i['peer_audits']['SOURCE_AUTHOR'])
i['bridge_source_ref']=pin(SRC/'w09_root_bridge.source.py');i['bridge_hdf_ref']=pin(SRC/'HDF.json')
assert i['bridge_source_ref']['sha256']=='22e642b51fb9f7a13b2dcb9db3057078f5479c16fb91fe0deded6b0109d1fb09'
assert i['bridge_hdf_ref']['sha256']=='048b118676757dc77f3d1d513ca7a852eb45e483ee2fb8224503b76b050956fc'
i['peer_audits']['SOURCE_AUTHOR']=pin(S/'w09.bridge08-source-author.actual-audit.root.json')
author=json.loads(Path(i['peer_audits']['SOURCE_AUTHOR']['path']).read_bytes());newraw=author['original_capture_ref']
oldraw=json.loads(Path(before['path']).read_bytes())['original_capture_ref']
for n,r in enumerate(i['fixed_refs']):
    p=Path(r['path'])
    if p.parent.name=='bridge-20261010-07':i['fixed_refs'][n]=pin(SRC/p.name)
    elif r==before:i['fixed_refs'][n]=i['peer_audits']['SOURCE_AUTHOR']
    elif r==oldraw:i['fixed_refs'][n]=newraw
for r in i['fixed_refs']:assert pin(Path(r['path']))==r
assert not NEW.exists();NEW.mkdir(parents=True)
ir=save(NEW/'source-inputs.json',encoded(i))
src=oldsource.replace(b'50930e0d982b5c7c570280cf2f9e65ad273256176ea3eaf637763e8926244c12',ir['sha256'].encode()).replace(b'bridge-20261010-07',b'bridge-20261010-08').replace(b'w09_br7_role_inputs_root',b'w09_br8_role_inputs_root').replace(b'BR7_PROPOSAL_CONTEXT',b'BR8_PROPOSAL_CONTEXT')
assert src.replace(ir['sha256'].encode(),b'50930e0d982b5c7c570280cf2f9e65ad273256176ea3eaf637763e8926244c12').replace(b'bridge-20261010-08',b'bridge-20261010-07').replace(b'w09_br8_role_inputs_root',b'w09_br7_role_inputs_root').replace(b'BR8_PROPOSAL_CONTEXT',b'BR7_PROPOSAL_CONTEXT')==oldsource
ast.parse(src);sr=save(NEW/'role_input_builder.source.py',src)
receipt=save(NEW/'rebase.prepared.root.json',encoded(dict(schema='researchos.w09-role-builder-constants-rebase.v1',issued_by='codex:/root',old_source_ref=pin(OLD/'role_input_builder.source.py'),new_source_ref=sr,old_inputs_ref=pin(OLD/'source-inputs.json'),new_inputs_ref=ir,complete_byte_inverse=True,builder_executed=False,Root_stage_calls=0,Main_Canon_Scope_Registry_writes=0,formal_acceptance=False,execution_grant=False)))
print(json.dumps(dict(preparation_ref=receipt,source_ref=sr,source_inputs_ref=ir,builder_executed=False),ensure_ascii=False))
