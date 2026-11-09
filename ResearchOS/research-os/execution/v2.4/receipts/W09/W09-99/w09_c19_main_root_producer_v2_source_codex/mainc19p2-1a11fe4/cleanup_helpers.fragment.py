class EvidenceFailure(RuntimeError):
    """Keep the original exception object and independent evidence errors."""
    def __init__(self,phase,primary_exception,secondary_errors,diagnostics):
        super().__init__(phase+': '+json.dumps(dict(original_error=repr(primary_exception) if primary_exception is not None else None,
            evidence_errors=secondary_errors),ensure_ascii=False))
        self.primary_exception=primary_exception
        self.secondary_errors=list(secondary_errors)
        self.diagnostics=diagnostics


def evidence_error(errors,phase,exc,label=None):
    errors.append(dict(phase=phase,label=label,exception_type=type(exc).__name__,error=repr(exc)))


def invoke(helper,root,label,argv,env,wall):
    out=root/(label+'.stdout.raw');err=root/(label+'.stderr.raw')
    result=None;primary=None;errors=[];receipt=None
    try:
        with out.open('xb') as stdout,err.open('xb') as stderr:
            result=helper.run_owned(argv,str(R),env,stdout,stderr,wall,creation_flags=0x08000000)
        require(job_closed(result),'OWNED_JOB_UNCLOSED_OR_EXCEPTION')
        require(result['error'] is None and result['actual_exit']==0 and result['timed_out'] is False,'FIRST_NATIVE_FAILURE_STOP')
    except BaseException as exc:primary=exc
    # Every observation is independent; no receipt failure masks the helper error.
    streams={}
    for name,path in (('stdout',out),('stderr',err)):
        streams[name+'_ref']=None
        try:
            if path.is_file():streams[name+'_ref']=pin(path)
        except BaseException as exc:evidence_error(errors,'invocation-stream-pin',exc,name)
    creation=result.get('creation_time_100ns') if type(result) is dict else None
    record=dict(argv=argv,cwd=str(R),public_environment=env,timeout_seconds=wall,result=result,
        exception=repr(primary) if primary is not None else None,
        actual_outer_exit=result.get('actual_exit') if type(result) is dict else None,individual_child_numeric_exit=None,
        creation_time_100ns_decimal=str(creation) if type(creation) is int else None,**streams,
        evidence_errors=errors,external_model_provider_requests=0,paid_provider_requests=0,production_DB_writes=0)
    try:receipt=save(root,label+'.invocation.json',record)
    except BaseException as exc:evidence_error(errors,'invocation-receipt-save',exc,label)
    try:
        print(json.dumps(dict(progress=label,receipt_ref=receipt,actual_outer_exit=record['actual_outer_exit'],
            creation_time_100ns_decimal=record['creation_time_100ns_decimal'],original_error=record['exception'],
            evidence_errors=errors,unsaved_invocation=record if receipt is None else None)),flush=True)
    except BaseException as exc:evidence_error(errors,'invocation-progress-write',exc,label)
    if primary is not None or errors:
        raise EvidenceFailure('INVOCATION_FAILED_NO_AUTOMATIC_RETRY',primary,errors,record) from primary
    return receipt,result


def observe_invocation(root,label,errors):
    row=dict(label=label,ref=None,record=None,verified=False,job_closed=False)
    path=root/(label+'.invocation.json')
    try:present=path.is_file()
    except BaseException as exc:
        evidence_error(errors,'invocation-presence',exc,label);return row
    if not present:
        evidence_error(errors,'invocation-missing',FileNotFoundError(str(path)),label);return row
    try:row['ref']=pin(path)
    except BaseException as exc:evidence_error(errors,'invocation-pin',exc,label)
    raw=None
    try:raw=path.read_bytes()
    except BaseException as exc:evidence_error(errors,'invocation-read',exc,label)
    if raw is not None:
        try:
            record=decode(raw);require(type(record) is dict,'INVOCATION_OBJECT_REQUIRED');row['record']=record
        except BaseException as exc:evidence_error(errors,'invocation-decode',exc,label)
    if row['ref'] is not None and raw is not None and row['record'] is not None:
        try:
            require(raw_pin(path,raw)==row['ref'],'INVOCATION_CHANGED_DURING_INSPECTION')
            row['verified']=True;row['job_closed']=job_closed(row['record'].get('result'))
        except BaseException as exc:evidence_error(errors,'invocation-closure',exc,label)
    return row


def close_stage_resources(kind,created,c,stage_root,output,guards):
    errors=[];observations=[];cleanups=[];packet_ref=None
    # Guard shutdown is in the outer finally, independent of all packet inspection.
    try:
        if created and kind=='run':
            for label in ('compiler-input-list','w09-c19-main-producer'):
                try:observations.append(observe_invocation(stage_root,label,errors))
                except BaseException as exc:
                    evidence_error(errors,'invocation-inspection',exc,label)
                    observations.append(dict(label=label,ref=None,record=None,verified=False,job_closed=False))
            producer=observations[-1]
            if producer['verified'] and producer['job_closed']:
                try:
                    if output.is_dir():packet_ref=capture_packet(c,stage_root)
                except BaseException as exc:evidence_error(errors,'packet-archive',exc)
    except BaseException as exc:evidence_error(errors,'packet-inspection',exc)
    finally:
        for label,guard in reversed(guards):
            row=dict(label=label,ref=None,closed=False,observation=None,receipt_saved=not created)
            # Close, classify and save are isolated; a save error does not erase a successful close.
            try:row['observation']=guard.close()
            except BaseException as exc:evidence_error(errors,'guard-close',exc,label)
            if row['observation'] is not None:
                try:row['closed']=guard_cleanup_ok(row['observation'])
                except BaseException as exc:evidence_error(errors,'guard-close-observation',exc,label)
                if created:
                    try:
                        row['ref']=save(stage_root,label+'-guard.cleanup.actual.json',row['observation']);row['receipt_saved']=True
                    except BaseException as exc:evidence_error(errors,'guard-cleanup-save',exc,label)
            cleanups.append(row)
    return dict(errors=errors,invocations=observations,guard_cleanups=cleanups,packet_ref=packet_ref,
        all_guards_closed=all(row['closed'] for row in cleanups) and len(cleanups)==len(guards),
        all_cleanup_receipts_saved=all(row['receipt_saved'] for row in cleanups),
        all_owned_jobs_closed=(kind=='prepare' or (len(observations)==2 and all(row['verified'] and row['job_closed'] for row in observations))))
