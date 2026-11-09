import pathlib,json,hashlib,datetime
E=pathlib.Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
inputs=json.loads((E/'INPUTS.json').read_bytes());mock=json.loads((E/'MOCK-RESULT.json').read_bytes())
for r in inputs:
 if sha(r['path'])!=r['sha256'] or sha(r['snapshot'])!=r['sha256']:raise RuntimeError('review input drift')
if len(mock['cases'])!=6 or not all(c['pass'] for c in mock['cases']):raise RuntimeError('mock results')
report={
 'schema':'researchos.independent-native-driver-v2-source-review.v1','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'status':'DRIVER_V2_SOURCE_ACCEPTED_FOR_NEW_EXACT_BOUND_SCOPE','driver_source_accepted':True,'controller_source_accepted':True,
 'reviewer':'codex:/root/product_host_independent_20261028','actual_native_runs':0,'productCore_runs':0,'productElectron_runs':0,'formal_increment':0,
 'fixed_driver_files':[{k:r[k] for k in ['path','sha256','bytes']} for r in inputs[:4]],
 'source_checks':[
  'Direct spawn with shell:false and raw file descriptors; PID/error/exit listeners/handle are registered before CDP attach. Child unref does not terminate it.',
  'Endpoint comes only from that spawned child stderr and is constrained to one127.0.0.1 browser WebSocket. Unique ros-app://desktop/ page is selected.',
  'Launch timeout, pre-endpoint process exit, CDP failure and page timeout preserve per-child terminal/unresolved evidence; no restart or shutdown is executed from catch.',
  'Normal close uses unchanged exact-PID/image/creation/SHA256 WM_CLOSE helper. Failure path never calls this helper.',
  'Wrapper validates all four v2 files are bound, verifies each scope reference, requires fresh isolated roots, and has no timeout kill/retry.',
  'Business assertions preserve actual CLI init, workspace identity, session identity, GUI reopen and CLI cold reopen chain; this is source inspection, not observed success.'
 ],
 'framework_disconnect_trace':[
  'client/browser.js close -> channel.close -> server/dispatchers/browserDispatcher.js close -> server/browser.js browserProcess.close',
  'server/chromium/chromium.js connectOverCDP sets browserProcess={close:doClose,kill:doClose}; doClose closes WebSocket transport then only its own mkdtemp artifacts',
  'server/transport.js closeAndWait calls WebSocket.close and waits for socket close; no Browser.close CDP command or OS process kill in this route',
  'CDP-connect catch uses same doClose. Unlike Electron.launch, it has no owned-product process handle and no taskkill callback'
 ],
 'pure_vm_results':mock,
 'limitations':['VM uses extracted exact source functions and global catch with mocked process/fs/CDP; no actual spawn, Windows WM_CLOSE, disconnect, GUI or Core was run.','If CDP disconnect itself stalls, controller termination may remain unresolved; no forced product cleanup is introduced.','Future native success must be independently reviewed; this report does not accept build05 native behavior or retire attempt01 failure.'],
 'scope_requirements':['Root must issue a new scope binding these exact four driver hashes, the current independently accepted build, and the reviewed Playwright tool closure.','Use fresh roots and preserve attempt01 state; no retry using old Electron.launch controller.'],
 'findings':[],
 'evidence_refs':[{'path':str(E/'INPUTS.json'),'sha256':sha(E/'INPUTS.json'),'bytes':(E/'INPUTS.json').stat().st_size},{'path':str(E/'MOCK-RESULT.json'),'sha256':sha(E/'MOCK-RESULT.json'),'bytes':(E/'MOCK-RESULT.json').stat().st_size},{'path':str(E/'failure-path-mock.cjs'),'sha256':sha(E/'failure-path-mock.cjs'),'bytes':(E/'failure-path-mock.cjs').stat().st_size}]
}
with (E/'REVIEW.json').open('x',encoding='utf8') as f:json.dump(report,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'driver_source_accepted':True,'sha256':sha(E/'REVIEW.json')}))
