"""Author packet only. Copies exact scoped source and public offline evidence."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

A=Path(__file__).resolve().parent
W=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/w14-native-create-clients-20261104')
RECEIPT=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/continue-cp597-20261104/clients')
OUT=A/'freeze-01'
SCOPE_PIN='eeb70473ce8c681c590f4f13288c622c6915ed08cbe7daee1a70609d15a7a873'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,v):
    with (OUT/name).open('x',encoding='utf-8',newline='\n') as f:
        if isinstance(v,dict): json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
        else:f.write(v)
def copy(src,relative):
    dst=OUT/relative
    assert not dst.exists(),str(dst)
    dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(src,dst)

assert sha(RECEIPT/'scope.json')==SCOPE_PIN
scope=json.loads((RECEIPT/'scope.json').read_bytes())
assert scope['owner']=='codex:/root/runtime_readiness'
assert scope['base_head']=='001f7e5a4d95152c8f83874a60d9fbd3bbace538'
assert not OUT.exists(),'Existing freeze: read back; never replay automatically'
paths=scope['production_paths']+scope['test_paths']
assert len(paths)==len(set(paths))==9
OUT.mkdir()
copy(RECEIPT/'scope.json','scope.json')
pins=[]
for rel in paths:
    src=W/rel
    assert src.is_file() and not src.is_symlink()
    pin=sha(src); baseline=scope['baseline_sha256'][rel]
    copy(src,'source-snapshot/'+rel)
    copy(A/'checked-source-01'/rel,'history/checked-source-01/'+rel)
    pins.append({'path':rel,'sha256':pin,'baseline_sha256':baseline,'changed':pin!=baseline})
assert sum(p['changed'] for p in pins)==8
assert next(p for p in pins if p['path']=='apps/cli/cli_verbs.go')['changed'] is False
for src,rel in [(A/'checks-01/go-tests.log','history/go-tests-01.log'),
                (A/'node-check-01.log','history/node-check-01.log'),
                (A/'checks-02/go-tests.log','go-tests-02.log'),
                (A/'checks-02/go-vet.log','go-vet-02.log'),
                (A/'node-check-02.log','node-check-02.log'),
                (A/'BASELINE.json','initial-baseline.json'),
                (Path('C:/Users/yqyyds/Documents/Codex/2026-11-04/task/cp598-native-create-core/INTERFACE.v1.json'),'core-interface.v1.json')]:
    copy(src,rel)
go_log=(OUT/'go-tests-02.log').read_text(encoding='utf-8-sig')
node_log=(OUT/'node-check-02.log').read_text(encoding='utf-8-sig')
assert 'PASS' in go_log and 'FAIL' not in go_log
assert '"checks":22' in node_log and '"status":"PASS"' in node_log
write('CHECKS.json',{
    'schema':'researchos.w14-native-create-client-author-checks.v1','status':'OFFLINE_CHECKED_AWAITING_INDEPENDENT_REVIEW',
    'first_go':{'started':'97ad6d','terminal':'d58aa4','exit':0,'test_pattern':'^TestNativeCreate','top_tests':3,'subcases':12},
    'first_node':{'terminal':'966d26','exit':0,'checks':19},
    'final_go':{'started':'8ce2b3','session':85267,'intermediate':'6ef471','terminal':'e1a0c8','test_exit':0,'vet_exit':0,'top_tests':3,'subcases':12},
    'final_node':{'terminal':'b893a3','exit':0,'checks':22},
    'go_exe':'D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go/bin/go.exe',
    'go_sha256':'d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490',
    'node_exe':'C:/nvm4w/nodejs/node.exe','node_sha256':sha(Path('C:/nvm4w/nodejs/node.exe')),
    'GOTOOLCHAIN':'local','GOPROXY':'off','GOSUMDB':'off','GOENV':'off',
    'GOMODCACHE':'D:/作品集/ResearchOS/research-os/.local/tools/gopath/pkg/mod',
    'GOCACHE':'Author-owned C checks-01/gocache only','GOTMPDIR':'Author-owned C checks-01/tmp and checks-02/tmp; fresh t.TempDir fixtures only',
    'coverage':['final actual raw digest and chosen bearer','closed Native DTO incl duplicate/extra/missing/trailing/expiry/host','unsupported NOT_SENT no fallback',
                'context/body/discovery changes NOT_SENT','Desktop sync/async body and header changes NOT_SENT',
                'Desktop replay same raw new bearer new proof','no selector/bearer in pending or renderer result','gate off and other methods zero new Native calls'],
    'limits':'Tests use fake Native dial and HTTP RoundTripper/VM recorders; existing packaged validator child, actual Native peer, Host origin transaction and GUI not executed',
    'real_native':0,'real_HTTP':0,'real_GUI':0,'real_model':0,'user_token_file_reads':0,'existing_DB_access':0,'formal_increment':0,'counter_reset':False})
write('AUTHOR-DIAGNOSTICS.json',{
    'scope_id':scope['scope_id'],'current_failed_batches':0,'uncertain_operations':[],
    'completed_mutations':[{'install_started':'95c213','terminal':'3b10cd','gofmt_exit':0},
                           {'source_update_terminal':'42ffaa','gofmt_exit':0,'first_checked_sources_preserved':True}],
    'baseline_read':'6442af/1ea799 exit0; worktree001f7e5a and production7 hashes matched scope before any edit',
    'default_read_limitation':'a28a26: default git worktree read Permission denied; elevated6442af succeeded; no denied mutation or repeated unknown action',
    'history':'All previous project failure origins/counters, consumed model probe and source evidence unchanged; no old probe or qualification replay',
    'dto_clarification':'Core author confirmed result top only kind+payload; frame_keys on unchanged INTERFACE.v1 refer to request; result extra client_id rejected',
    'unchanged_allowpath':'apps/cli/cli_verbs.go; final send point in cli_v2 covers all callers without credentialFor or context construction proof',
    'runtime_not_authorized_by_packet':True,'formal_increment':0,'counter_reset':False})
write('README.md','''# W14 client fresh-create Native pilot — author delivery

This packet freezes six changed production files, two new pure tests, and the unchanged allowed cli_verbs.go against CP598 scope. No Main commit, registry/checkpoint change, public protocol schema change, real Native/HTTP/GUI/model or user-token/old-DB access occurred. Scope-nine is an upper bound; the actual changed set is eight. This is not W14 formal acceptance or runtime authorization.

Only RESEARCHOS_NATIVE_CREATE_PILOT=1 enables session.create proof. Default sends the same envelope bytes and makes no new Native/discovery calls. Other methods and original three Native actions/credential renewal keep their behavior. Unsupported Native, invalid result or changed request fails NOT_SENT with no legacy fallback. Private constants avoid a dependency on unintegrated Host Go symbols; Core's frozen public interface and result-top clarification are recorded.

CLI computes the commitment from the bytes passed to NewRequest after choosing the actual bearer, calls the verified current Host Native pipe, rejects nonclosed result JSON and host/expiry mismatches, then compares context/raw again before setting a transient X-ResearchOS-Native-Attestation selector. The real consumer must verify that selector against its current private Host witness and actual HTTP bytes/authentication; a client label cannot authorize anything.

Desktop waits until exact stringify and preflight child completion; the private Main callback attests final raw bytes plus the copied final bearer. It then rechecks the original body, original headers, discovery identity and validator resource before POST. Neither bearer nor attestation_ref is saved in pending command state or returned to renderer. A replay retains the original public raw command, obtains the current bearer through the existing provider, and obtains fresh proof for that attempt. possiblySent/ACK command lifetimes are preserved across later NOT_SENT results. The attestation action never bootstraps or reads session.json; the existing provider remains responsible for ordinary renewal.

Final author checks: three Go top-level tests plus twelve subcases, go vet, and twenty-two Node checks passed. Tests poison/replace all real Native/net/http/spawn boundaries and use only new fixture discovery files. Node VM substitutes the packaged validator child and HTTP recorder; it still exercises the actual final-send control flow. Consequently this packet does not prove the real packaged Native bridge, renderer GUI, validator executable, actual Host witness transaction or end-to-end writer-origin persistence. Integration must use rebuilt normal release inventories and independently reviewed Core/schema paths.

First passing source/logs and final raw logs are retained. No failed origin was cleared or duplicated. All tool sessions listed in diagnostics reached an actual terminal result. Do not run model/resource probes or old UNKNOWN approvals. Independent source review and Root integration remain required.
''')
inventory=[]
for p in sorted(OUT.rglob('*')):
    if p.is_file():inventory.append({'path':p.relative_to(OUT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size})
write('MANIFEST.json',{'schema':'researchos.w14-native-create-clients-author-manifest.v1','status':'FROZEN_FOR_INDEPENDENT_REVIEW',
    'at':datetime.now(timezone.utc).isoformat(),'scope_sha256':SCOPE_PIN,'scope_id':scope['scope_id'],'base_head':scope['base_head'],
    'worktree':str(W),'owner':scope['owner'],'source_pins':pins,'actual_changed_count':8,'changed_production_count':6,'new_test_count':2,
    'unchanged_allowpath':'apps/cli/cli_verbs.go','raw_and_support_files':inventory,'formal_increment':0,'counter_reset':False,
    'real_native':0,'real_HTTP':0,'real_model':0,'user_token_file_reads':0,'existing_DB_access':0,'independent_review_required':True})
target=RECEIPT/'author'/'freeze-01'
assert not target.exists(),'Receipt already exists: inspect first'
shutil.copytree(OUT,target)
assert sha(target/'MANIFEST.json')==sha(OUT/'MANIFEST.json')
print(json.dumps({'status':'FROZEN_FOR_INDEPENDENT_REVIEW','manifest_sha256':sha(OUT/'MANIFEST.json'),
    'receipt':str(target),'source_pins':pins,'support_count':len(inventory),'real_native':0,'real_HTTP':0,'formal_increment':0}))
