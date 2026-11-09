import json,hashlib
from pathlib import Path
W=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99')
N=W/'fresh_main23_root_caller_registration_source_codex/main23root-20261010-04'
def doc(p):return json.loads(Path(p).read_bytes())
def pin(p):
 b=Path(p).read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
h=doc(N/'HDF.json');mf=doc(N/'MF.json');ins=doc(N/'source-inputs.json')
print(json.dumps(dict(pins=[pin(N/x) for x in ['HDF.json','MF.json','main23_root.source.py','root-calling-contract.source.json']],hdf={k:v for k,v in h.items() if k!='actual_Source_identity'},mf_keys=list(mf),members=len(mf['members']),inputs_keys=list(ins),inputs_nonrefs={k:v for k,v in ins.items() if k not in ['references']},inverse=doc(N/'exact-inverse.json'),finite_keys=list(doc(N/'finite-M4-source-controls.json')),peer_binding=doc(W/'main23_qualification_time_contract_independent_review_codex/review-20261010-01/actual-peer-60922.binding.json')),ensure_ascii=False),flush=True)
