import subprocess,sys
from pathlib import Path
N=Path(__file__).parent;text=(N/'verify_binary_sd_contract.py').read_text(encoding='utf8')
old="s['native_ACE_flag_drift_reported']==4";assert text.count(old)==1
text=text.replace(old,"s['native_ACE_flag_drift_reported']==[85,109,129,149]")
p=N/'verify_binary_sd_contract_r2.py'
with p.open('x',encoding='utf8')as f:f.write(text)
raise SystemExit(subprocess.run([sys.executable,'-B','-X','utf8',str(p)]).returncode)

