from verify import *

gates=[]
def require(name,condition):
    assert condition,name
    gates.append(name)
def rows(conn,table):
    conn.row_factory=sqlite3.Row
    return [dict(r) for r in conn.execute('SELECT * FROM '+table)]
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),default=lambda b:{'bytes':b.hex()})
def same(a,b):return sorted(map(canonical,a))==sorted(map(canonical,b))

try:
    root=OUT/'snapshots-active/TestConfigurationUpgradeActiveQueueRecovery'
    a=sqlite3.connect((root/'source22.sqlite').as_uri()+'?mode=ro',uri=True)
    b=sqlite3.connect((root/'restored23.sqlite').as_uri()+'?mode=ro',uri=True)
    require('source schema exactly 1..22',a.execute('SELECT min(version),max(version),count(*) FROM schema_migrations').fetchone()==(1,22,22))
    require('target schema exactly 1..23',b.execute('SELECT min(version),max(version),count(*) FROM schema_migrations').fetchone()==(1,23,23))
    require('no source identities',a.execute("SELECT count(*) FROM sqlite_master WHERE name='client_command_identities'").fetchone()[0]==0)
    require('new identities empty',b.execute('SELECT count(*) FROM client_command_identities').fetchone()[0]==0)
    before={t:rows(a,t) for t in ('client_sessions','client_queue_fences','client_command_queue','client_control_requests','client_control_receipts','idempotency','resource_effects','domain_versions','runtime_dispatches','domain_objects')}
    after={t:rows(b,t) for t in before}
    require('all eight loss mutation probes nonempty',all(len(after[t])>0 for t in ('client_sessions','client_queue_fences','client_command_queue','client_control_requests','client_control_receipts','idempotency','resource_effects','domain_versions')))
    require('seven queue identities retained',len(before['client_command_queue'])==len(after['client_command_queue'])==7)
    newer={r['command_id']:r for r in after['client_command_queue']}
    require('queue generation and sequence retained',all(r['generation']==newer[r['command_id']]['generation'] and r['queue_sequence']==newer[r['command_id']]['queue_sequence'] for r in before['client_command_queue']))
    require('four unresolved queues become UNKNOWN',sum(r['state']=='UNKNOWN' for r in after['client_command_queue'])==4)
    require('terminal CONSUMED and DROPPED unchanged',all(r['state']==newer[r['command_id']]['state'] for r in before['client_command_queue'] if r['state'] in ('CONSUMED','DROPPED')))
    require('control request reconciles',len(after['client_control_requests'])==1 and after['client_control_requests'][0]['state']=='RECONCILING')
    require('idempotency rows byte typed equality',same(before['idempotency'],after['idempotency']))
    require('dispatch rows equality and no dispatch',same(before['runtime_dispatches'],after['runtime_dispatches']) and len(after['runtime_dispatches'])==0)
    rec=load(AUTHOR/'closed-source22-05.json')
    oldrun=json.loads(next(r['body'] for r in before['domain_objects'] if r['kind']=='Run' and r['id']==rec['run_id']))
    newrun=json.loads(next(r['body'] for r in after['domain_objects'] if r['kind']=='Run' and r['id']==rec['run_id']))
    require('run identity epoch retained and status reconciles',oldrun['lease_epoch']==newrun['lease_epoch']==rec['run_lease_epoch'] and newrun['status']=='RECONCILING')
    require('lease token replaced and expired',newrun['lease_token_hash']!=oldrun['lease_token_hash'] and newrun['lease_expires_at']=='1970-01-01T00:00:00Z')
    require('run revision incremented once',newrun['revision']==oldrun['revision']+1)
    oldeffects=sorted(before['resource_effects'],key=lambda r:r['sequence']);neweffects=sorted(after['resource_effects'],key=lambda r:r['sequence'])
    require('original effect history retained',all(r in neweffects for r in oldeffects))
    require('effect UNKNOWN retained with fence append',len(oldeffects)==3 and len(neweffects)==4 and json.loads(oldeffects[-1]['body'])['state']=='UNKNOWN' and json.loads(neweffects[-1]['body'])['state']=='UNKNOWN' and neweffects[-1]['sequence']==oldeffects[-1]['sequence']+1)
    require('domain version history retained',all(r in after['domain_versions'] for r in before['domain_versions']))
    a.close();b.close()
    provenance=load(OUT/'input-provenance.json')
    require('5922 compiler inputs unchanged after tests',all(Path(p).is_file() and sha(p)==v for p,v in provenance['resolved_compiler_inputs'].items()))
    scope=load(SCOPE);construction=load(MAIN/scope['construction_scope']['path']);pins=load(MAIN/construction['historical_pins_ref']['path'])
    require('502 historical source pins unchanged after tests',all(sha(SRC/item['relative_path'])==item['sha256'] for item in pins['files']))
    native=load(AUTHOR/'fresh-native-pins.json')
    require('29 native resources unchanged after tests',all(sha(item['path'])==item['sha256'] for item in native['entries']))
    require('helper executable unchanged',sha(MAIN/'.local/builds/historical22-active-queue-helper-20261015/historical22-active-queue-05.test.exe')==load(AUTHOR/'build-helper-05.invocation.json')['test_exe_sha256'])
    save('snapshot-assertions.json',{'assertion_count':len(gates),'assertions':gates,'source_snapshot':pin(root/'source22.sqlite'),'target_snapshot':pin(root/'restored23.sqlite'),'loss_probe_tables_executed':8,'effects_field':'body.state (prior diagnostic body.status returned null; corrected here)','effect_states_before':[json.loads(r['body'])['state'] for r in oldeffects],'effect_states_after':[json.loads(r['body'])['state'] for r in neweffects],'counts_before':{t:len(v) for t,v in before.items()},'counts_after':{t:len(v) for t,v in after.items()}})
    log({'kind':'snapshot-independent-assertions','native_exit':0,'assertion_count':len(gates),'loss_probe_tables_executed':8,'result':'PASS'})
    print('independent snapshot assertions PASS',len(gates))
except Exception as exc:
    log({'kind':'snapshot-check-failure','native_exit':1,'error':str(exc),'passed_assertions':gates});raise
