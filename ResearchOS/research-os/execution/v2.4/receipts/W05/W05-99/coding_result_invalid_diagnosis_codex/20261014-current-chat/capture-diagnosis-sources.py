import pathlib,json,hashlib,subprocess,datetime
E=pathlib.Path(__file__).parent;ROOT=pathlib.Path('D:/作品集/ResearchOS/research-os');S=pathlib.Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/coding-any-combined-build-20261014');P=pathlib.Path('C:/Users/yqyyds/.codex/researchos-resource-cache/normal-coding-any-a7ec7ebf-20261014');COMMIT='a7ec7ebf2d53848ea163b6115667b3e3761a6bd2';sha=lambda b:hashlib.sha256(b).hexdigest();inputs=[]
for name in ['apps/desktop/main/lib/desktop-management.js','internal/domain/client_runtime_coding_windows.go','internal/domain/client_runtime_setup_windows.go','tests/ui/desktop/coding-authorization-boundary.test.mjs']:
 b=(S/name).read_bytes();assert b==subprocess.check_output(['git','-C',str(ROOT),'show',COMMIT+':'+name]);p=E/'source'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);entry={'source':str(S/name),'path':p.relative_to(E).as_posix(),'sha256':sha(b),'bytes':len(b),'commit':COMMIT}
 if name.startswith('apps/desktop'):assert (P/name).read_bytes()==b;entry['installed_package_same_bytes']=True
 inputs.append(entry)
for n in ['23-current-refrozen-plan.ui.txt','24-native-current-confirmation.json','25-native-confirmation-checked.json','27-config-result.ui.txt']:
 p=ROOT/'execution/v2.4/receipts/W05/W05-99/normal_desktop_attach_retry09_codex/20261014-current-chat'/n;b=p.read_bytes();inputs.append({'source':str(p),'sha256':sha(b),'bytes':len(b),'root_record_only':True})
(E/'source-and-root-evidence-binding.json').write_text(json.dumps(inputs,ensure_ascii=False,indent=2),encoding='utf8')
print('bound',len(inputs))
