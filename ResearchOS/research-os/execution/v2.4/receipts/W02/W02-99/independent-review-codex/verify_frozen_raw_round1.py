import collections,datetime,hashlib,json,pathlib,subprocess,sys
R=pathlib.Path('D:/作品集/ResearchOS/research-os');O=pathlib.Path(__file__).resolve().parent;B=O.parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
checks=[];refs={}
def check(id,ok,detail=None):
 row={'id':id,'ok':bool(ok),'detail':detail};checks.append(row);print(json.dumps(row,ensure_ascii=False));assert ok,id
def bind(p):refs[str(p)]=sha(p);return read(p)
def mapped(name):
 text=name.replace('\\','/');marker='/.local/worktrees/codex-w0299/'
 return R/text.split(marker,1)[1] if marker in text else pathlib.Path(name)
pin=bind(B/'parent_inputs_codex.json');repair=bind(B/'g01_repair_inputs_codex.json');handoff=bind(B/'handoff_codex.json')
run1=B/handoff['gates']['W02-G01']['run'];run3=B/handoff['gates']['W02-G03']['run'];old=B/repair['prior_run']
rawcounts={};sourceinputs={}
for label,run in [('G01',run1),('G03',run3),('G01-original-failed',old)]:
 manifest=bind(run/'manifest.json');record=bind(run/'receipt.json')
 check(label+'-manifest-all-bytes',all((run/p).is_file() and sha(run/p)==h for p,h in manifest.items()),len(manifest))
 refs.update({str(run/p):h for p,h in manifest.items()});rawcounts[label]=len(manifest)
 check(label+'-assertion-inventory',bool(record['checks']) and record['assertions']==len(record['checks'])==len(record['assertion_ids'])==len(set(record['assertion_ids'])) and record['assertion_ids']==[r['id'] for r in record['checks']])
 check(label+'-no-formal-promotion',record['owned_acceptance_ids']==record['formal_cases_accepted']==[] and record['whole_card_accepted'] is False and all(record[k]==0 for k in ['new_provider_calls','new_service_operations','new_gui_operations']))
 drift=[]
 for name,h in record['source_inputs_sha256'].items():
  p=mapped(name)
  if p.name in ['parent_driver.py','dispatcher_fixture.py','dispatch_parent.py'] and p.parent==B:
   p=run/'driver-sources'/p.name
  if not p.is_file() or sha(p)!=h:drift.append(str(p))
  else:sourceinputs[str(p)]=h
 check(label+'-actual-inputs-and-driver-archive',not drift,{'inputs':len(record['source_inputs_sha256']),'drift':drift})
 for c in record['commands']:
  check(label+'-command-'+c['label'],all(sha(run/c[k]['path'])==c[k]['sha256'] for k in ['stdout','stderr']) and read(run/(c['label']+'.command.json'))==c,{'exit':c['exit_code'],'argv':c['argv']})
one=read(run1/'receipt.json');three=read(run3/'receipt.json');prior=read(old/'receipt.json')
check('G01-actual17-pass',one['status']=='PASS' and len(one['checks'])==17 and all(x['ok'] is True for x in one['checks']))
check('G03-actual21-pass',three['status']=='PASS' and len(three['checks'])==21 and all(x['ok'] is True for x in three['checks']))
check('original-G01-failure-preserved',prior['status']=='FAIL' and any(not x['ok'] for x in prior['checks']))
old2=bind(B/'run-20261005T204259Z-bb25f6d59445/receipt.json')
check('old-G02-misclassification-preserved',old2['status']=='PENDING_INTEGRATION' and {'W02-G02-EXACT_PARENT_BINDING','W02-G02-EVALUATION_UI_RESTRICTED_MAPPING'}<={r['id'] for r in old2['checks'] if not r['ok']})
files=pin['build_sources']|repair['additional_build_sources'];clean=bind(run1/'clean-source-manifest.json')
check('517-clean-current-source-bytes',len(clean)==517 and clean==files and all(sha(R/p)==h for p,h in clean.items()))
tracked=set(subprocess.check_output(['git','ls-files'],cwd=R,text=True).splitlines())
check('clean-source-all-tracked-no-product-binaries',set(clean)<=tracked and not any(p.endswith(('.exe','.dll')) or '/node_modules/' in p for p in clean))
check('locked-used-tools-current',all(sha(pathlib.Path(pin['tools'][t]['path']))==pin['tools'][t]['sha256'] for t in ['python','go','node','npm_cli','electron']))
builds={c['label']:c for c in one['commands']};oldcommands={c['label']:c for c in prior['commands']}
check('actual-control-and-cli-builds',all(builds['build-'+n]['exit_code']==0 and builds['build-'+n]['argv'][1:3]==['build','-trimpath'] and builds['build-'+n]['argv'][-1]=='./apps/'+('cli' if n=='researchos' else 'control') for n in ['control','researchos']))
check('cold-isolated-build-environment',all(c['fixed_environment']['GOTOOLCHAIN']=='local' and c['fixed_environment']['GOENV']=='off' and c['fixed_environment']['GOPROXY']=='off' and c['fixed_environment']['GOSUMDB']=='off' and c['fixed_environment']['GOFLAGS']=='-mod=readonly' and '/scratch/gocache' in c['fixed_environment']['GOCACHE'].replace('\\','/') for c in one['commands']))
version=bind(run1/'cli-version.stdout.txt')
check('actual-cli-version-and-unsupported-command',builds['cli-version']['exit_code']==0 and version['protocol']=='researchos-client/2' and version['status']=='COMPLETED' and builds['cli-unimplemented']['exit_code']==3 and 'NOT_IMPLEMENTED' in (run1/'cli-unimplemented.stderr.txt').read_text())
reused=[r for r in one['checks'] if isinstance(r['detail'],dict) and 'reused_passed_current_subcheck' in r['detail']]
check('exact-passed-subcheck-reuse',all(r['detail']['receipt_sha256']==sha(old/'receipt.json') and r['detail']['raw_manifest_sha256']==sha(old/'manifest.json') and next(x for x in prior['checks'] if x['id']==r['id'])['ok'] is True for r in reused),[r['id'] for r in reused])
go=[json.loads(l) for l in (old/'minimum-go-tests.stdout.txt').read_text().splitlines() if l]
passed=[x['Test'] for x in go if x.get('Action')=='pass' and 'Test' in x]
check('three-minimum-tests-actual-nonempty',set(passed)=={'TestJSON','TestUTF16AndFieldOrder','TestOpenSettings'} and not any(x['Action'] in ['fail','skip'] for x in go) and oldcommands['minimum-go-tests']['exit_code']==0,passed)
check('modules-verified-actual',oldcommands['verify-go-modules']['exit_code']==0 and 'all modules verified' in (old/'verify-go-modules.stdout.txt').read_text())
spec=pathlib.Path(pin['spec_root']);checksreport=bind(old/'v24-schema-api-static.stdout.txt')
check('minimum-frozen-schema-api-static-actual',oldcommands['v24-schema-api-static']['exit_code']==0 and checksreport['status']=='PASS' and bool(checksreport['checks']),{'scope':'SPEC_PACKAGE_STATIC; not full A03 runtime acceptance','count':len(checksreport['checks'])})
check('all-recorded-spec-input-hashes',all(sha(spec/p)==h for p,h in pin['spec_files'].items()),len(pin['spec_files']))
check('current-runtime-protocol-frozen',sha(R/'internal/api/contracts/client.protocol.schema.json')==pin['spec_files']['contracts/client.protocol.schema.json'])
renderer=R/pin['sample'];closure=bind(B/'renderer_reuse_closure_codex.json')
check('renderer18-inputs-and-raw-current',len(pin['renderer_inputs'])==18 and all(sha(R/p)==h for p,h in pin['renderer_inputs'].items()) and all(sha(renderer/p)==h for p,h in pin['renderer_evidence'].items()))
check('renderer-token-import-closure',sha(R/closure['additional_import'])==closure['import_sha256'] and hashlib.sha256(subprocess.check_output(['git','show','265137d9:'+closure['additional_import']],cwd=R)).hexdigest()==closure['import_sha256'] and closure['additional_import'] in (R/'apps/web/src/main.jsx').read_text())
identity=bind(B/'build_identity_supplement_codex.json');info=(run1/'buildinfo-control.stdout.txt').read_text()
check('actual-buildinfo-derived-identity-honest',identity['buildinfo_sha256']==sha(run1/'buildinfo-control.stdout.txt') and identity['implementation_sha256']==sha(R/'internal/api/v2.go') and identity['vcs_revision'] in info and 'vcs.modified=true' in info and identity['core_build_id']=='core-'+identity['vcs_revision'][:12] and identity['core_build_id_runtime_observed'] is False)
vendor=bind(R/'third_party/mu.MANIFEST.json');component=bind(R/'execution/v2.4/component_lock.json');route=bind(R/'execution/v2.4/route.json')
check('5083-current-mu-tracked-bytes',len(vendor['entries'])==component['mu']['file_count']==5083 and all(sha(R/p)==v['sha256'] for p,v in vendor['entries'].items()))
check('sole-frozen-route',route['selected_route']=='MU_FORK' and route['mu']['commit']==component['mu']['commit'] and route['jev']['status']=='NOT_RUN' and route['fallback']['status']=='NOT_TRIGGERED')
cases=bind(run3/'dispatcher-cases.json');allinv=[]
for c in cases:
 p=run3/c['receipt'];raw=bind(p);allinv.append(raw['invocation_id']);fixture=run3/'dispatcher-fixture'
 check('actual-dispatch-'+c['label'],sha(p)==c['receipt_sha256'] and raw['status']==c['expected_status']==c['actual_status'] and raw['exit_code']==c['expected_exit']==c['actual_exit'] and all(sha(fixture/raw[k]['path'])==raw[k]['sha256'] for k in ['stdout','stderr']),{'status':raw['status'],'exit':raw['exit_code'],'child_exit':raw['child_exit_code'],'ids':raw['assertion_ids']})
check('dispatch-invocations-unique',len(allinv)==len(set(allinv)),len(allinv))
secretrow=next(x for x in three['checks'] if x['id']=='W02-G03-DISPATCH_SECRET_ARG');secret=bind(run3/secretrow['detail']['receipt'])
check('actual-secret-argv-refused-before-child',secret['status']=='SECRET_IN_ARGUMENTS' and secret['exit_code']==7 and secret['child_exit_code'] is None and 'argv' not in secret)
red=next(c for c in cases if c['label']=='SECRET_REDACTION');redpath=run3/red['receipt'];needle='synthetic-w0299-quote"slash\\value'
check('secret-sentinel-sanitized-all-raw',all(needle not in p.read_text() and json.dumps(needle)[1:-1] not in p.read_text() for p in redpath.parent.iterdir() if p.is_file()) and read(redpath)['assertion_ids']==['[REDACTED]'])
check('G01-G03-scratch-cleaned',all(read(run/'cleanup.json')['exit_code']==0 and read(run/'cleanup.json')['absent'] is True and not pathlib.Path(read(run/'cleanup.json')['target']).exists() for run in [run1,run3,old]))
refs.update(sourceinputs)
check('review-reference-inputs-stable',all(sha(pathlib.Path(p))==h for p,h in refs.items()))
result={'phase':'FROZEN_G01_G03_RAW_REVIEW_ONLY','status':'PASS_IN_SCOPE_PENDING_REGISTERED_G02_AND_REUSE_HANDLER','source_head_at_read':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),'checks':checks,'raw_manifest_file_counts':rawcounts,'passed_prior_subcheck_reuse_count':len(reused),'reference_hashes':refs,'new_Go_GUI_provider_service_calls':0,'card_accepted':False,'formal_cases_accepted':[],'reviewed_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
with (O/'frozen_raw_review.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps({'status':result['status'],'checks':len(checks),'reused_checks':len(reused)}))
