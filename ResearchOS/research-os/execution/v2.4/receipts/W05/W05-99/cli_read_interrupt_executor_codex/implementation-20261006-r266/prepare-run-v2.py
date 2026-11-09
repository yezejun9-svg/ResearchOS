import pathlib
D=pathlib.Path(r'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/cli_read_interrupt_executor_codex/implementation-20261006-r266')
s=(D/'run.py').read_text(encoding='utf8')
s=s.replace("RESEARCHOS_GO=str(G/'bin/go.exe'))", "RESEARCHOS_GO=str(G/'bin/go.exe'),RESEARCHOS_NODE='C:/nvm4w/nodejs/node.exe',RESEARCHOS_MU_BUNDLE=str(R/'.local/w0599-queue-integration/mu-worker.mjs'))")
s=s.replace("'RESEARCHOS_GO']", "'RESEARCHOS_GO','RESEARCHOS_NODE','RESEARCHOS_MU_BUNDLE']")
s=s.replace("if completed.returncode: print(completed.stdout.decode('utf8','replace')[-12000:]);print(completed.stderr.decode('utf8','replace')[-3000:])", "if completed.returncode:\n  for line in completed.stdout.splitlines():\n   try:row=json.loads(line)\n   except:continue\n   if row.get('Action')=='fail' or row.get('OutputType')=='error':print(json.dumps(row,ensure_ascii=False))\n  print(completed.stderr.decode('utf8','replace')[-3000:])")
(D/'run-v2.py').write_text(s,encoding='utf8')
print('created run-v2.py; original missing Node/bundle invocation preserved')