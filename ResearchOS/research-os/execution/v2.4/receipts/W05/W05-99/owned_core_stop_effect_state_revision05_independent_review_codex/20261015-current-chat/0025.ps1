$e='D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/owned_core_stop_effect_state_revision05_independent_review_codex/20261015-current-chat'
@"
import pathlib,json,difflib
E=pathlib.Path(r'$e')
p=E/'seal.py';s=p.read_text(encoding='utf-8-sig')
s=s.replace("i=='0024'","i=='0025'").replace("'0024.stdout.txt','0024.stderr.txt','0024.exit.txt'","'0025.stdout.txt','0025.stderr.txt','0025.exit.txt'").replace('0024 stdout/stderr/exit','0025 stdout/stderr/exit')
s=s.replace("item['captures']=[pin(E/rec[k]) for k in ['stdout','stderr','nativeexit']]", "item['captures']=[pin(E/rec[k]) for k in ['stdout','stderr','nativeexit'] if (E/rec[k]).exists()];item['absent_capture_files']=[rec[k] for k in ['stdout','stderr','nativeexit'] if not (E/rec[k]).exists()]")
s=s.replace("classification='reviewer_missing_parent_agents_diagnostic'", "classification='reviewer_missing_parent_agents_diagnostic' if i=='0001' else 'reviewer_seal_expected_stdout_absence_diagnostic'")
s=s.replace("sum(x['kind']=='shell' for x in nonzero)==1", "sum(x['kind']=='shell' for x in nonzero)==2")
(E/'seal2.py').write_text(s,encoding='utf-8');(E/'seal2.patch').write_text(''.join(difflib.unified_diff(p.read_text(encoding='utf-8-sig').splitlines(True),s.splitlines(True),fromfile='seal.py',tofile='seal2.py')),encoding='utf-8')
p=E/'failure-ledger.json';v=json.loads(p.read_text());v['new_groups'].append(dict(id='STOP-R5-REVIEW-D02',kind='REVIEWER_SEAL_DIAGNOSTIC',command='0024',native_exit=1,error='Initial failed 0001 produced no stdout file; sealing originally assumed all stream files existed',recovery='0025 records absent_capture_files without fabricating an empty raw stream',product_failure=False));p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=E/'review.md';p.write_text(p.read_text(encoding='utf-8')+'\n封存诊断：0024 因 0001 失败发生在 stdout 文件建立前而触发 FileNotFoundError；0025 明确登记该缺失，不补造空 stdout。诊断及原失败脚本保留，不构成新增 Source 缺陷。最终封存命令的 stdout/stderr/exit 在其返回后闭合，作为邻接回执保留并显式排除自身哈希循环。\n',encoding='utf-8')
"@ | Set-Content -Encoding utf8 "$e/repair_seal.py"
& 'C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe' -B -X utf8 "$e/repair_seal.py"
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
& 'C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe' -B -X utf8 "$e/seal2.py"
exit $LASTEXITCODE
