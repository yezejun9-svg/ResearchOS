from pathlib import Path
import json,hashlib,ast
N=Path(__file__).parent
B=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99')
S=B/'integration_codex/native-broker4-positive-serve-root-1791513411000/serve_one_positive_broker4.actual_owned.py'
A=B/'integration_codex/native-broker4-positive-root-api-1791513411000/root_public_api_broker4.actual.py'
H=B/'root_native_concrete_phase_helpers_revision_codex/nhr1-1a11e7f5205729390aaee9f47b28ce6/root_concrete_approval_helper.py'
CTL=B/'native_controller_retained_window_revision_codex/ctl4-1a11e7f5205729390aaee9f47b28ce6/root_native_migration_controller.py'
def pin(p):
 b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
assert pin(A)['sha256']=='6eeae42516cdb6cad02f09555747c103e4e736c0ca4752dfe210a66c975fb04b' and pin(A)['bytes']==14698
assert pin(H)['sha256']=='122f586885a2f3cd8141f4697175655d03441667603fc378cdac662e21a65ac2' and pin(H)['bytes']==29098
assert pin(CTL)['sha256']=='e7538c580d2e07217512e036e00272b3be94cb11551ace6885cc46316a67b3b3' and pin(CTL)['bytes']==42696
refs=[pin(p) for p in [S,A,H,CTL]]
for folder in [H.parent,CTL.parent,B/'root_native_concrete_helpers_independent_review_codex/nhr1r-20261009-source-review']:
 for name in ['HDF.json','MF.json','report.md']:
  p=folder/name
  refs.append(pin(p))
old_config='native-broker4-controller-config-root-1791513411000/controller.public.config.json'
new_config='native-cleanup-controller-source-root-1791517434000/controller.public.config.json'
old_assert='assert config_plain["sha256"]=="48c06dc2c88326a98cd785b364d6daf5fad363292a7a4f97fd209938d54273b2" and config_plain["bytes"]==1178613'
parse='''# Root supplies the exact frozen C12 config pin at every invocation.
assert len(sys.argv) >= 5 and sys.argv[-4] == "--config-sha256" and sys.argv[-2] == "--config-bytes"
expected_config_sha=sys.argv[-3]; expected_config_bytes_text=sys.argv[-1]
assert len(expected_config_sha)==64 and all(c in "0123456789abcdef" for c in expected_config_sha)
assert expected_config_bytes_text.isascii() and expected_config_bytes_text.isdigit() and not expected_config_bytes_text.startswith("0")
expected_config_bytes=int(expected_config_bytes_text)
sys.argv=sys.argv[:-4]
assert O.is_dir() and not O.is_symlink() and O.resolve()==O
'''
boundary='''
 assert c["hc"]["CaseID"]=="t12cl149d6f49321"
 assert cfg["ControllerSource"]["sha256"]=="sha256:e7538c580d2e07217512e036e00272b3be94cb11551ace6885cc46316a67b3b3" and cfg["ControllerSource"]["bytes"]==42696
 assert Path(c["hc"]["RootProgram"]["path"]).resolve().parent==R/".local/native-cleanup-compile-env-1791516889000/programs"
 protected_outputs=[Path(cfg["ControllerDirectory"]).resolve(),Path(c["hc"]["OutputDirectory"]).resolve(),Path(c["hc"]["RootProgram"]["path"]).resolve().parent,Path(c["hc"]["BuildRoot"]).resolve(),Path(cfg["Environment"]["TEMP"]).resolve()]
 assert all(not O.is_relative_to(p) for p in protected_outputs)
'''
outputs=[];changes=[]
for source,name,out in [(S,'serve_one_positive_c12.actual_owned.py','native-cleanup-positive-serve-root-1791517434000'),(A,'root_public_api_c12.actual.py','native-cleanup-positive-root-api-1791517434000')]:
 raw=source.read_bytes();s=raw.decode();newline='\r\n' if '\r\n' in s else '\n';s=s.replace('\r\n','\n');original=s
 replacements=[('O=Path(__file__).resolve().parent','O=B/"integration_codex/'+out+'"'),(old_config,new_config),('config_raw=C.read_bytes()',parse+'config_raw=C.read_bytes()'),(old_assert,'assert config_plain["sha256"]==expected_config_sha and config_plain["bytes"]==expected_config_bytes'),(' c=controller.context(config_ref);assert c["hc"]["Case"]=="positive-replay"',' c=controller.context(config_ref);assert c["hc"]["Case"]=="positive-replay"'+boundary)]
 if source==S:
  replacements += [('str(Path(__file__).resolve()),"--child"]','str(Path(__file__).resolve()),"--child","--config-sha256",expected_config_sha,"--config-bytes",str(expected_config_bytes)]'),('env,stdout,stderr,1440,creation_flags','env,stdout,stderr,1800,creation_flags')]
 for old,new in replacements:
  assert s.count(old)==1,(name,old);s=s.replace(old,new)
 ast.parse(s)
 inverse=s
 for old,new in reversed(replacements):assert inverse.count(new)==1;inverse=inverse.replace(new,old)
 assert inverse==original
 (N/'base').mkdir(exist_ok=True)
 (N/'base'/source.name).write_bytes(raw)
 p=N/name;p.write_bytes(s.replace('\n',newline).encode())
 outputs.append(pin(p));changes.append({'candidate':str(p),'base':pin(source),'exact_byte_inverse':inverse.replace('\n',newline).encode()==raw,'replacements':replacements})
assert refs[:4]==[pin(p) for p in [S,A,H,CTL]]
(N/'input-pins.json').write_text(json.dumps(refs,indent=2),encoding='utf-8')
(N/'source-replacements.json').write_text(json.dumps(changes,indent=2),encoding='utf-8')
print(json.dumps({'source_only':True,'candidates':outputs,'native':False,'config_read_or_created':False,'outer_timeout_correction':'1440 to1800 explicitly authorized; old S10 unchanged'}))
