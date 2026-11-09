"""Freeze scoped client repairs; preserves rejected v1 and all failure evidence."""
from datetime import datetime,timezone
import hashlib,json,shutil
from pathlib import Path
A=Path(__file__).resolve().parent
W=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/w14-native-create-clients-20261104')
R=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/continue-cp597-20261104/clients')
Q=Path('C:/Users/yqyyds/Documents/Codex/2026-11-04/task/cp597-continuation/w14-native-create-clients-independent-review-01')
OUT=A/'freeze-02'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def copy(src,name):
    dest=OUT/name
    assert not dest.exists(),str(dest)
    dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
def write(name,v):
    with (OUT/name).open('x',encoding='utf-8',newline='\n') as f:
        if isinstance(v,dict):json.dump(v,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
        else:f.write(v)
old=json.loads((A/'freeze-01/MANIFEST.json').read_bytes())
old_pin='4b0adde5874c424eb43b1414cdfe36d6d919888f4c3fa69ecd41e4704e8a1c02'
assert sha(A/'freeze-01/MANIFEST.json')==old_pin
for root in (A/'freeze-01',R/'author/freeze-01'):
    assert sha(root/'MANIFEST.json')==old_pin
    for p in old['raw_and_support_files']:assert sha(root/p['path'])==p['sha256'],p['path']
review_pin='8215291ba3e98de8774132c042a4bc4228945fdf61a3fa516e9c554af31fc102'
assert sha(Q/'source-review.json')==review_pin
scope=json.loads((R/'scope.json').read_bytes())
assert sha(R/'scope.json')==old['scope_sha256']
assert not OUT.exists(),'Existing outcome: read back, no replay'
OUT.mkdir()
pins=[];repair=[]
for prior in old['source_pins']:
    rel=prior['path'];pin=sha(W/rel)
    copy(W/rel,'source-snapshot/'+rel)
    pins.append({'path':rel,'sha256':pin,'baseline_sha256':prior['baseline_sha256'],'changed':pin!=prior['baseline_sha256']})
    if pin!=prior['sha256']:repair.append(rel)
assert set(repair)=={'apps/cli/cli_native.go','apps/cli/cli_native_attestation_test.go',
    'apps/desktop/main/lib/native.js','apps/desktop/main/lib/http-wire.js','apps/desktop/main/lib/ipc.js','tests/ui/native-create-attestation-fixture.cjs'}
for src,name in [(R/'scope.json','scope.json'),(A/'checks-03/go-tests.log','go-tests-03.log'),
    (A/'checks-03/go-vet.log','go-vet-03.log'),(A/'node-check-03.log','node-check-03.log'),
    (A/'node-existing-pure-01.log','node-existing-pure-01.log'),(A/'run-existing-pure.mjs','run-existing-pure.mjs')]:copy(src,name)
for name in ['source-review.json','go-independent-tests.log','go-independent-checks.json','independent-go-extra.txt',
             'independent-node-attempt-02.cjs','node-independent-checks-attempt-02.json','node-independent-attempt-02.log']:
    copy(Q/name,'rejected-v1-review/'+name)
assert 'PASS' in (OUT/'go-tests-03.log').read_text(encoding='utf-8-sig')
assert '"checks":29' in (OUT/'node-check-03.log').read_text(encoding='utf-8-sig')
existing=(OUT/'node-existing-pure-01.log').read_text(encoding='utf-8-sig')
assert 'pass 43' in existing and 'fail 0' in existing
checks={'schema':'researchos.w14-native-create-client-author-checks.v2','status':'AUTHOR_REPAIRED_AWAITING_INDEPENDENT_REVIEW',
    'Go':{'started':'aa0855','session':75550,'terminal':'58f67a','test_exit':0,'vet_exit':0,'top_tests':3,'subcases':16},
    'Node':{'terminal':'eaa814','exit':0,'checks':29},
    'existing_pure_Node':{'started':'c65393','session':73796,'intermediate':'cf279b','terminal':'98edd6','exit':0,'tests':43,'pass':43,'fail':0,
       'files':['tests/ui/desktop/coding-authorization-boundary.test.mjs','tests/ui/desktop/desktop-management-boundary.test.mjs'],
       'live_IO':'exec/spawn/net/http explicitly poisoned; one Node process; author-owned fresh TEMP/TMP'},
    'toolchain':{'Go':'D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go/bin/go.exe','Go_sha256':'d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490',
       'Node':'C:/nvm4w/nodejs/node.exe','Node_sha256':sha(Path('C:/nvm4w/nodejs/node.exe')),'GOPROXY':'off','GOSUMDB':'off','GOTOOLCHAIN':'local','GOENV':'off',
       'module_cache':'Read-only locked .local/tools/gopath/pkg/mod','build_cache':'Author-owned C checks-01/gocache','fixtures':'Fresh C checks-03/tmp and node-existing-tmp'},
    'limitations':'Pure mocks only. Existing full http-wire-boundary suite requires a real HTTP listener and validator child, so not run under this scope; real bridge/GUI/Host transaction/business acceptance not established.',
    'real_native':0,'real_HTTP':0,'real_GUI':0,'real_model':0,'old_DB_access':0,'user_token_file_reads':0,'formal_increment':0,'counter_reset':False}
write('CHECKS.json',checks)
write('AUTHOR-DIAGNOSTICS.json',{'rejected_freeze01_manifest_sha256':old_pin,'blocking_review_sha256':review_pin,
    'existing_failure_origins':['CLIENT-P1-001','CLIENT-P1-002','CLIENT-P1-003'],
    'failure_evidence':'Original 21ca24 Go exit1/vet0, Node009d44/c0fb6a source counterexamples and original replay harness correction retained in independent QA report/artifacts; do not duplicate Root origin indices or reset counts.',
    'source_repairs':{'CLIENT-P1-001':'strict syntax/duplicate/trailing/UTF8 before exact case-sensitive required key map then typed decode',
       'CLIENT-P1-002':'New attestation raw lane only waits full EOF, hard absolute timeout and 8192 cap; legacy actions keep early JSON completion',
       'CLIENT-P1-003':'Main private synchronous verifyOrigin exactly true after every await/resource/body/header check, immediately before post with no intervening await'},
    'author_mutations':[{'Go_install':'93db5f','exit':0},{'Node_install':'317e0d','exit':0}],
    'resolved_tool_pending':'g35:34 ->93db5f;g35:35 ->aa0855/session75550 ->58f67a;g35:42 ->317e0d;g35:43 ->64c527. Never replayed pending writes.',
    'readonly_lookup_nonzero':['483288','7bd97b'],'readonly_lookup_meaning':'Optional candidate filename/regex lookup found no matches; not a product run or a failed test; kept separately from the real QA failure origins.',
    'uncertain_operations':[],'source_repair_not_acceptance':True,'formal_increment':0,'counter_reset':False})
write('README.md','''# Client repair freeze02 — independent review required

Rejected freeze01, all29 evidence pins in both C and D, original four Go failures, two chunked-reply failures, one microtask-origin failure and QA's separately diagnosed replay-fixture correction remain intact. CLIENT-P1-001/002/003 are existing origins; this packet references them and does not reset or duplicate their Root indices.

Only six scoped paths changed from rejected v1. CLI JSON checks strict syntax/UTF8/duplicate/trailing first, then the exact case-sensitive top2/payload5 key sets, then typed decoding. Four case-alias/collision regressions all stop before fake HTTP. The new Desktop attestation raw lane collects through EOF with an absolute deadline and8192-byte cap; split trailing objects/garbage, no EOF and oversize refuse. Existing three Native actions retain their original early parsed-JSON completion; the only production rawReply=true caller is createClientAttestor. No bootstrap/renew/token-file read was added.

Desktop Main provides a private synchronous current-origin guard. Wire finishes every async value operation and rechecks body/header/resource, then requires guard===true immediately before post enters synchronous http.request, with no await in between. Exceptions, Promise/nontrue or changed Host/PID/instance are NOT_SENT. The exact queued Promise/microtask discovery mutation from QA is a regression. Gateoff envelope bytes/calls, public protocol/schema, pending possiblySent barrier, replay raw preservation and replacement-bearer proof acquisition remain unchanged.

Author verification: Go3top+16subcases and vet passed58f67a; pure Node29 checks passed eaa814; existing pure coding-authorization and desktop-management fixtures43passed98edd6 in one Node process with live IO poisoned and fresh C temp files. Complete old http-wire-boundary tests start an HTTP listener and validator child and were not authorized here. Real Native, HTTP, GUI, model/provider, existing DB and user-token-file accesses remain0. No Main commit, registry or checkpoint write occurred. Tests do not prove an actual Native peer, packaged release inventory, Host witness transaction, durable writer origin or full W14 acceptance. Root integration and independent review are still required.
''')
inventory=[{'path':p.relative_to(OUT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(OUT.rglob('*')) if p.is_file()]
write('MANIFEST.json',{'schema':'researchos.w14-native-create-clients-author-manifest.v2','status':'FROZEN_REPAIRS_FOR_INDEPENDENT_REVIEW',
    'at':datetime.now(timezone.utc).isoformat(),'owner':scope['owner'],'scope_id':scope['scope_id'],'scope_sha256':old['scope_sha256'],
    'base_head':old['base_head'],'worktree':str(W),'rejected_freeze01_manifest_sha256':old_pin,'blocking_review_sha256':review_pin,
    'source_pins':pins,'repair_paths_from_rejected_v1':repair,'actual_changed_count':8,'changed_production_count':6,'new_test_count':2,
    'unchanged_allowpath':'apps/cli/cli_verbs.go','raw_and_support_files':inventory,'independent_review_required':True,
    'real_native':0,'real_HTTP':0,'real_model':0,'user_token_file_reads':0,'old_DB_access':0,'formal_increment':0,'counter_reset':False})
dest=R/'author/freeze-02';assert not dest.exists(),'Existing D outcome: read back first';shutil.copytree(OUT,dest)
assert sha(dest/'MANIFEST.json')==sha(OUT/'MANIFEST.json')
print(json.dumps({'status':'FROZEN_REPAIRS_FOR_INDEPENDENT_REVIEW','manifest_sha256':sha(OUT/'MANIFEST.json'),'support_count':len(inventory),
    'source_pins':pins,'rejected_freeze01_29pins_changed':0,'real_native':0,'real_HTTP':0,'formal_increment':0}))
