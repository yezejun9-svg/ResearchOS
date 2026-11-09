from review_driver import *
# All ordinary command results and ledger writes have completed before this separate seal emitter.
files={p.relative_to(E).as_posix():{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in E.rglob('*') if p.is_file() and p.name!='FINAL-SEAL.json' and 'commands/030-final-seal/' not in p.relative_to(E).as_posix()}
save(E/'FINAL-SEAL.json',dict(schema='researchos.react-source14-independent-review-seal.v1',candidate_commit=SHA,candidate_tree='de59625ee5c1d360c741c95ec3f84b6f2764bb0e',scope_sha256='859ea46d295cdaa1508cf85c7433b3e5383bedfb952f4ad0c1a36cad60a267f0',verdict='NO_BLOCKING_FINDINGS',formal_increment=0,manifest=files,excluded=['FINAL-SEAL.json (self)','commands/030-final-seal/* (separate finalizer envelope; numeric result retained after emission)']))
print(json.dumps(dict(seal_sha256=hashlib.sha256((E/'FINAL-SEAL.json').read_bytes()).hexdigest(),files=len(files))))
