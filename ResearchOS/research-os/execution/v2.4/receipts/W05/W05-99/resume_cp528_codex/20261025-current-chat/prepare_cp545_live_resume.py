import subprocess,sys
from pathlib import Path
N=Path(__file__).parent;t=(N/'042-cp541-live-resume.py').read_text(encoding='utf8')
pairs=[('041-selector-cp541','057-selector-cp545'),('cp541','cp545'),('CP541','CP545'),("==541","==545"),("==327","==331"),("==2128","==2186"),("'checkpoint':541","'checkpoint':545"),("'ownership':327","'ownership':331"),("'mixed_records_preserved':2128","'mixed_records_preserved':2186"),('0381a3429492be6096c48ce98968aeb8b61a472dc6b1cb9600ffded4bddf51b4','2a4a6b04341c927bc20487faae7d32ea813a320791818c46d1fc6d4377a35a70'),('PROGRESS_C57_HOST_WRITER_AND_NATIVE_FIXTURES_PLUS_INDEPENDENT_PERSISTENT_CONTROL_FINDINGS','PROGRESS_CP541_TO_CP545_C51_PRESEAL_AND_LIFETIME_FIX_NATIVE_SD_CONTRACT_FINDINGS')]
for a,b in pairs:
 assert a in t,a
 t=t.replace(a,b)
p=N/'058-cp545-live-resume.py'
with p.open('x',encoding='utf8')as f:f.write(t)
raise SystemExit(subprocess.run([sys.executable,'-B','-X','utf8',str(p)]).returncode)

