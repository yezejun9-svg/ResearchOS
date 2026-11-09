from review_tools import E,W,A,S,HEAD,TREE,BASE,read,write,pin,guards
import datetime,decimal,hashlib,json,pathlib

def verify_pin(item,root=None):
    p=pathlib.Path(item['path']) if root is None else root/item['path']
    actual=pin(p)
    assert actual['sha256']==item['sha256'],str(p)
    if 'bytes' in item: assert actual['bytes']==item['bytes'],str(p)
    return actual

def budget(p):
    native=read(p);run=native['final_run'];prefix='runtime-local-launch/'+run['id']+'/'
    rows=[json.loads(x['body']) for x in native['budget_ledger']]
    rows=[x for x in rows if x['provider_request_id'].startswith(prefix)]
    assert len(rows)==6
    checks=[]
    for epoch in range(1,4):
        request=prefix+str(epoch)
        hold,=[x for x in rows if x['provider_request_id']==request and x['operation']=='RESERVE']
        release,=[x for x in rows if x['provider_request_id']==request and x['operation']=='RELEASE']
        assert hold['run_id']==release['run_id']==run['id'] and hold['project_id']==release['project_id']==run['project_id']
        assert hold['provider_event_id']==request and release['provider_event_id']==request+'/released'
        assert hold['reservation_id'] is None and release['reservation_id']==hold['id']
        assert hold['policy_id']==release['policy_id'] and hold['money']==release['money']
        assert decimal.Decimal(hold['money']['amount'])==0 and hold['cost_basis']=='UPPER_BOUND' and release['cost_basis']=='ACTUAL'
        for row in [hold,release]:
            digest='sha256:'+hashlib.sha256(json.dumps({k:v for k,v in row.items() if k!='receipt_hash'},sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
            assert row['receipt_hash']==digest
            assert datetime.datetime.fromisoformat(row['occurred_at'].replace('Z','+00:00')).tzinfo is not None
        checks.append(dict(epoch=epoch,hold_id=hold['id'],release_id=release['id'],exact_binding=True,receipt_hashes_valid=True,timestamps_parse=True))
    assert run['lease_epoch']==3
    assert len(native['activations'])==2
    assert len([x for x in native['queue'] if x['state']=='CONSUMED'])==4
    assert len([x for x in native['queue_receipts'] if x['kind']=='command.consumed'])==4
    return dict(source=pin(p),run=run['id'],epoch=3,checks=checks,consumed_commands=4,consumption_receipts=4)

def main():
    source=guards();verified=[]
    original=read(E/'input-verification.json')
    for key in ['scope','author_source_manifest','author_attempt_ledger']:
        verified.append(verify_pin(original[key]))
    for item in original['verified_author_inputs']: verified.append(verify_pin(item))
    scope=read(S)
    assert sorted(scope['allowed_source_files'])==sorted(x['path'] for x in read(A/'source-manifest.json')['source_files'])
    for key in ['review_ref','review_manifest_ref','architecture_ref']:
        verified.append(verify_pin(scope[key],pathlib.Path('D:/作品集/ResearchOS/research-os')))
    for item in read(E/'runtime-inputs.json')['inputs']: verified.append(verify_pin(item))
    for item in read(E/'overlay-inputs.json'):
        for key in ['previous','copy','current_target']: verified.append(verify_pin(item[key]))
    attempts=[]
    for ledger_name in ['attempt-ledger.json','attempt-ledger-resume.json']:
        ledger=read(E/ledger_name)
        for a in ledger['attempts']:
            verified.append(verify_pin(a['command']))
            command=read(pathlib.Path(a['command']['path']))
            for key in ['stdout','stderr']: verified.append(verify_pin(command[key]))
            assert command['exit']==a['exit']
            for suffix in ['source-before.json','source-after.json']:
                assert read(E/a['name']/suffix)==source
            attempts.append(a)
    budgets=[]
    for name in ['TestProductMuSecondPauseResumeNative','TestProductMuSecondPauseModelAcrossHeartbeatNative','TestProductMuSecondPauseToolAcrossHeartbeatNative']:
        p=E/'native'/name/'canonical-evidence.json';d=read(p)
        if 'AcrossHeartbeat' in name:
            assert d['heartbeat_wait_milliseconds']>=17000
            assert d['heartbeat_after']>d['heartbeat_before']
        budgets.append(budget(p))
    revocations=[]
    for kind in ['cancel','owner','goal','lease']:
        p=E/'native/TestProductMuSecondPauseRevocationAcrossHeartbeatNative'/(kind+'-heartbeat')/'canonical-evidence.json';d=read(p)
        assert d['heartbeat_wait_milliseconds']>=17000 and d['heartbeat_after']>d['heartbeat_before']
        assert d['bridge']['cancelled'] is True and d['epoch3_activation_count']==0
        assert d['queue_consumed_before']==d['queue_consumed_after']==2 and d['actual_host_tool_calls']==1
        revocations.append(dict(source=pin(p),classification=d['classification'],no_successor=True,queue_unchanged=True))
    probe=E/'native-resume/TestReviewMuSecondPauseAcrossHeartbeatNative'
    assert read(probe/'after-second-pause.json')['pause_state']=='PAUSED_CONFIRMED'
    budgets.append(budget(probe/'canonical-evidence.json'))
    rollback_path=E/'native-resume/TestReviewMuBudgetFailureRollsBackNativeSuccessor/canonical-evidence.json'
    rollback=read(rollback_path)
    assert rollback['same_state'] is True and rollback['before']==rollback['after']
    assert 'invalid prior runtime local launch release' in rollback['scan_error']
    write(E/'resume-verification.json',dict(source=source,verified_inputs=verified,budgets=budgets,revocations=revocations,rollback=pin(rollback_path),attempts=attempts,formal_increment=0))
    print(json.dumps(dict(verified_pins=len(verified),budget_trajectories=len(budgets),revocations=len(revocations),attempts=len(attempts))))

if __name__=='__main__': main()
