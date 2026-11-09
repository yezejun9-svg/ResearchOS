import hashlib,json
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os');HERE=Path(__file__).resolve().parent;WT=ROOT/'.local/worktrees/product-v1-native-preparation-wiring-20261105';OUT=HERE/'product-v1-native-preparation-overlay-directory-setup.json';assert not OUT.exists()
created=[]
for rel in ('internal/qualificationprobe','cmd','cmd/researchos-qualification-helper'):
 p=WT/rel;assert p.resolve().is_relative_to(WT.resolve())
 if p.exists():assert p.is_dir() and not p.is_symlink() and not p.is_junction()
 else:p.mkdir();created.append(str(p))
for rel in ('internal/qualificationprobe','cmd/researchos-qualification-helper'):assert not list((WT/rel).iterdir())
record=dict(status='EMPTY_PHYSICAL_DIRECTORIES_FOR_GO_VET_OVERLAY_CWD_ONLY',worktree=str(WT),created=created,source_file_writes=0,vet_disabled=False,native_model_calls=0,scope='Exact controlled temporary build worktree; no tracked source or historical artifacts changed.')
OUT.write_bytes((json.dumps(record,indent=2)+'\n').encode('utf8'));print(json.dumps(dict(receipt=str(OUT),sha256=hashlib.sha256(OUT.read_bytes()).hexdigest(),created=len(created))))
