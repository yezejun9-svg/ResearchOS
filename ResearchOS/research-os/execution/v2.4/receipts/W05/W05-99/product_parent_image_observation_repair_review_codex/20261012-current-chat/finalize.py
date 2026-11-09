from pathlib import Path
import hashlib,json,subprocess,datetime
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[6]
WT=ROOT/'.local/worktrees/w05-desktop-parent-image-observation-repair-20261012'
AUTHOR=OUT.parents[1]/'product_parent_image_observation_repair_codex/20261012-current-chat'
CANDIDATE='040d297627e2cfc5de2d6b9e770acc7bdf4f9ab7';BASE='860a8935c8fffe4a1671eafa177e7fc5a053158a'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(n,v):(OUT/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=WT,text=True).strip()==CANDIDATE
status=subprocess.check_output(['git','status','--porcelain'],cwd=WT);assert not status.strip();(OUT/'candidate-tracked-status.txt').write_bytes(status)
assert sha(AUTHOR/'source-bundle-final.json')=='3ac0eb9ef64c8e1790ae27f6c9dee4b3244a1d79a1c1b353a9de0ab3fe449df4'
b=read(AUTHOR/'source-bundle-final.json')
for row in b['files']:assert sha(AUTHOR/row['path'])==row['sha256']
for row in b['source']['files']:assert sha(WT/row['path'])==row['sha256']==sha(OUT/'source'/row['path'])
for row in b['builds']:assert sha(Path(row['path']))==row['sha256']
v=read(OUT/'input-verification.json');assert v['checks']==v['passed']==56 and not v['failures']
counts=[]
for label,np,ns in [('observation',6,6),('causal',1,0)]:
 assert read(OUT/(label+'.invocation.json'))['exit_code']==0
 events=[]
 for line in (OUT/(label+'.stdout')).read_bytes().splitlines():
  try:events.append(json.loads(line))
  except ValueError:pass
 terminal=[e for e in events if e.get('Action') in ['pass','fail','skip']];assert terminal==read(OUT/(label+'.summary.json'))
 parents=sum(e['Action']=='pass' and 'Test'in e and '/'not in e['Test'] for e in terminal);subs=sum(e['Action']=='pass' and '/'in e.get('Test','') for e in terminal)
 assert (parents,subs)==(np,ns) and all(e['Action']=='pass' for e in terminal)
 counts.append(dict(invocation=label,parent_passes=parents,subtest_passes=subs,failures=0,skips=0))
causal=(OUT/'causal.stdout').read_text(encoding='utf-8')
assert 'exactImage_128=refused observed_256=accepted size=204521984' in causal and 'no_signal=true' in causal
report=dict(schema='researchos.parent-image-observation-independent-review/1',decision='ACCEPT',acceptance_scope='SOURCE_AND_NATIVE_OBSERVATION_FIXTURE_ONLY',blocking_findings=[],candidate=CANDIDATE,base=BASE,source_paths=2,
 author_bundle_sha256=sha(AUTHOR/'source-bundle-final.json'),scope_sha256='ad8f5eaa6e9570b11bfeb638e64be7974094c4f0e3e8e17f42cdc28fc959c2d6',
 binding=dict(checks=56,passed=56,author_receipts=45,exact_two_git_source_objects=True,original_failed_boot_reference_verified=True,core_base_bundle_and_prior_acceptance_verified=True,original_decoded_pointers_valid=True,control_sha256='4e421f23af5a6c82dd5c6a90729120499adc0bcfd2977f70ba6de71b119397ad',runtime_verifier_sha256='70b422d9ce5fe4a9e0502fef5f4834f78f8dc6151ab5776d5787f14d5dcb1e25',binary_vcs_revision=CANDIDATE,binary_vcs_modified=False,independent_rebuild=False),
 independent_tests=counts,
 actual_observation=dict(pid=53188,image_bytes=204521984,image_sha256='8d205e25b40da3ada4a08c92f32bfbd8e8d38edb4bfe443deea77fc9de685bac',os_query_path=True,unchanged_exactImage_128MiB_refused=True,new_observed_256MiB_accepted=True,created_ns_and_alive_match=True,signals_sent=0,window_commands_sent=0),
 source_review=[
  dict(reference='ops/supervisor/release_process_windows.go:55',result='exactImage body is byte-for-byte unchanged against accepted Core860: absolute .exe path, no reparse, regular file and 128 MiB launch/release gate. ReleaseEngine bootstrap/prepare/switch/rollback, ControlFixtureDriver.Start and NativeFixtureDriver.Start still call exactImage.'),
  dict(reference='ops/supervisor/release_process_windows.go:99',result='processImageDigest receives an existing OS process handle and obtains QueryFullProcessImageName; caller cannot supply an alternate wire image path. Only this observed digest route uses the new helper.'),
  dict(reference='ops/supervisor/release_process_windows.go:114',result='observedProcessImageDigest rejects relative/non-exe/reparse/nonregular/over-256MiB inputs; io.LimitReader reads at most 256 MiB plus one overflow byte, SHA256 covers complete accepted file, before/after size and mtime plus byte count reject observed changes.'),
  dict(reference='ops/supervisor/release_process_windows.go:167',result='Alive retains exact PID/CreatedNS, liveness and digest comparison; Stop retains independent handle CreatedNS and digest recheck. The shared helper therefore also affects identity checks inside Stop, but adds no call, launch, release or stop authorization. Reviewer issued no Stop/kill.'),
  dict(reference='internal/host/desktop_management_windows.go:79',result='Unchanged managed-parent verification still reobserves exact original OS parent identity, checks os.Getppid and uses existing SameUser SID verification. None of these authorities comes from a management frame.')
 ],
 test_coverage=['Actual original Electron ObserveProcess/Alive positive, mismatched CreatedNS and SHA256 negative. Independent same-path causal check proves old launch/release gate still rejects the exact 195 MiB image accepted for observation.','Current process and actual EOF-exiting Node identity passed; Node/control/verifier small-image digests agree with unchanged exactImage.','Observed 128 MiB+1 and exact 256 MiB files accepted with full streamed hash equality; 256 MiB+1 rejected. All those over-128 files remain rejected by exactImage and NativeFixtureDriver.Start before launch.','Native owned junction, relative path, directory and absent image rejected. No skipped tests or failed reviewer invocation.'],
 frozen_author_regression=dict(verified=True,rerun=False,parent_passes=2,subtest_passes=0,failures=0,skips=0,evidence='attempt09-frozen-process-regression raw Go JSON and summary verified against frozen receipt SHA and final binary tuple; two real control generations exit=0 and separate Mu/verifier synthetic qualification. Author final synthetic responses=2; not counted as reviewer model calls.'),
 limitations=['Only source and bounded native observation component accepted. Root actual Desktop first-use has not been retried by this reviewer and is not PASS.','Accepted Core24 matrix was referenced by frozen hash, not repeated or reaccepted under this review. Integrated Main/native qualification still requires its own execution evidence.','Final control/verifier binaries were source/hash/VCS checked, not independently rebuilt or relaunched by this reviewer. Their frozen author lifecycle tests were reconstructed from original raw records.','No actual model, external provider, paid endpoint, public tunnel or protected holdout. Observation acceptance does not imply a real model qualification.','The 256 MiB bound remains finite; larger future parent images will still fail closed. Concurrent file-change guards were source-reviewed; no deterministic in-flight file-mutation hook was added to production code.'],
 history=['All 45 original receipts, including author unsuccessful/diagnostic attempts, remain unchanged. No reviewer test failure occurred.','Scoped PowerShell deletion of this new review cache was rejected by automatic approval review: blocked by policy. Cache retained and excluded from manifest; no alternate deletion attempted.'],
 actual_model_calls=0,synthetic_model_calls=0,external_calls=0,paid_calls=0,public_tunnel_calls=0,formal_acceptance_delta=0,parent_acceptance_delta=0,
 writes='Only this new independent receipt directory. New Go test supplied via virtual overlay; candidate/source/Main/Canon/contracts/old receipts unchanged. No original-process signal, window command or kill.'
 )
write('independent-review.json',report)
(OUT/'README.md').write_text('''# Parent image observation 独立审查

**ACCEPT — SOURCE_AND_NATIVE_OBSERVATION_FIXTURE_ONLY**。候选 `040d297627e2cfc5de2d6b9e770acc7bdf4f9ab7`，仅2文件；无阻断项。

56/56绑定检查通过，覆盖45份原始receipt、原失败启动记录、2份Git源码及control/verifier来源元组。`exactImage` 函数逐字未变，启动/发布仍受128MiB限制；观察路径采用256MiB+1有界读取与前后大小/mtime检查，原PID/CreatedNS/hash及SameUser SID验证保留。

独立运行7父、6子测试通过，无失败/跳过。对仍运行的原Electron PID53188执行只读检查：204521984 bytes，同一OS路径在原128MiB函数被拒绝，在新256MiB观察函数通过，hash/CreatedNS/Alive吻合。错误身份、junction、非规范路径、大小边界和启动拒绝均通过。未发进程信号、窗口指令或kill。

作者最终两项control/Mu/verifier原生回归以冻结原始输出复核，未重新运行Core24或模型链。完整Electron真实首用与正式验收未接受；本轮真实及合成模型调用均0，external/paid/tunnel为0，formal/parent +0。最终二进制核验来源，未独立重建。

新缓存定向删除被自动审批审查以 `blocked by policy` 拒绝，已保留并排除证据清单；未尝试其他删除方式。
''',encoding='utf-8')
canon={}
for name in ['current_spec.json','checkpoint.json','step_state.json','path_ownership.json','commands.json']:
 p=ROOT/'execution/v2.4'/name;canon[name]=dict(sha256=sha(p),facts={k:v for k,v in read(p).items() if k in ['revision','head','status']})
write('main-canon-end-observation.json',dict(head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),canon=canon,note='Read-only; concurrent parent work outside reviewer scope.'))
excluded={'cache':'Retained reviewer Go/test cache; scoped deletion blocked by policy.'}
files=[]
for p in sorted(OUT.rglob('*')):
 rel=p.relative_to(OUT)
 if p.is_file() and rel.parts[0]not in excluded and p.name not in ['receipt_manifest.json','review-seal.json']:
  files.append(dict(path=rel.as_posix(),bytes=p.stat().st_size,sha256=sha(p)))
write('receipt_manifest.json',dict(schema='researchos.independent-review-manifest/1',created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),decision='ACCEPT',acceptance_scope=report['acceptance_scope'],candidate=CANDIDATE,model_calls=0,excluded_retained_runtime_roots=excluded,files=files))
for row in files:assert sha(OUT/row['path'])==row['sha256']
seal=dict(decision='ACCEPT',acceptance_scope=report['acceptance_scope'],files=len(files),decision_sha256=sha(OUT/'independent-review.json'),manifest_sha256=sha(OUT/'receipt_manifest.json'))
write('review-seal.json',seal);print(json.dumps(seal))
