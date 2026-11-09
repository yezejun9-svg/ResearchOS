from pathlib import Path
import json, hashlib
R = Path(r'D:\作品集\ResearchOS\research-os')
D = Path(__file__).resolve().parent
P = R/'execution/v2.4/receipts/W09/W09-99/main_w09_formal_router_sequence_root/fix-20261010-01'
SEED = R/'execution/v2.4/receipts/W09/W09-99/w09_br6_actual_root/actual-20261010-01/seed-7960283ac5b549e28bfe045d7f90b59e/context-seed.json'
def pin(path):
    raw=Path(path).read_bytes()
    return dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
seed=json.loads(SEED.read_bytes())
vector=seed['version_vector']
out=dict(seed_ref=pin(SEED),candidate_ref=pin(P/'formal_profile_w09.candidate.py'),
    before_ref=pin(P/'formal_profile_w09.before.py'),proposal_ref=pin(P/'proposal.root.json'),
    current_Main_ref=pin(R/'execution/v2.4/formal_profile_w09.py'),seed_keys=list(seed),
    vector_keys=list(vector),vector_groups={key:dict(count=len(vector[key]),paths=[item['path'] for item in vector[key]])
        for key in ('spec_files','source_files','input_files','lock_files','tool_files')},
    registered_commands=seed['registered_commands'],private_or_live_Canon_read=False)
with (D/'input-inventory.json').open('xb') as f:f.write((json.dumps(out,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps(out,ensure_ascii=False))
