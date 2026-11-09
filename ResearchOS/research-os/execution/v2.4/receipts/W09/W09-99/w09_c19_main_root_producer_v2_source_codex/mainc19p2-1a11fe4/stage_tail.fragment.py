    except BaseException as exc:primary=exc;error=repr(exc)
    finally:
        closed=close_stage_resources(kind,created,c,stage_root,output,guards)
    cleanups=closed['guard_cleanups'];errors=closed['errors'];packet_ref=closed['packet_ref']
    receipts=[row['ref'] for row in closed['invocations'] if row['ref'] is not None]
    all_closed=closed['all_guards_closed'];all_jobs_closed=closed['all_owned_jobs_closed']
    success=success and all_closed and closed['all_cleanup_receipts_saved'] and not errors
    if kind=='run':success=success and packet_ref is not None and len(receipts)==2 and all_jobs_closed
    result=dict(schema='researchos.w09-main-c19-stage-closed.v2',stage=kind,
        status=('PREPARED_ALL_GUARDS_CLOSED' if kind=='prepare' else 'MAIN_C19_NATIVE_PACKET_CLOSED_PENDING_INDEPENDENT_REVIEW') if success else 'FAILED_NO_AUTOMATIC_RETRY',
        error=error,original_exception_type=type(primary).__name__ if primary is not None else None,
        original_invocation_diagnostics=primary.diagnostics if isinstance(primary,EvidenceFailure) else None,
        original_invocation_errors=primary.secondary_errors if isinstance(primary,EvidenceFailure) else [],
        cleanup_errors=errors,summary=summary,native_packet_ref=packet_ref,request_ref=request_ref,
        invocation_refs=receipts,invocation_observations=closed['invocations'],guard_cleanups=cleanups,
        all_guards_closed=all_closed,all_cleanup_receipts_saved=closed['all_cleanup_receipts_saved'],
        actual_formal_consumers=False,formal_case_accepted_delta=0,all_owned_jobs_closed=all_jobs_closed,
        individual_unobserved_native_exits=None,external_model_provider_requests=0,paid_provider_requests=0,
        Main_source_written=False,Canon_written=False,process_loss_requires_explicit_Root_reconciliation=True,automatic_retry=False)
    published=False
    if created:
        try:
            if success and kind=='prepare':
                result.update(summary);result['guard_cleanup_refs']=[row['ref'] for row in cleanups]
                save(actual,'prepare.ready.json',result)
            else:save(stage_root,'validation.closed.json',result)
            published=True
        except BaseException as exc:
            evidence_error(errors,'stage-result-save',exc);result['status']='FAILED_NO_AUTOMATIC_RETRY';success=False
    try:
        print(json.dumps(dict(status=result['status'],stage=kind,receipt_root=str(stage_root),error=error,
            cleanup_errors=errors,all_guards_closed=all_closed,all_owned_jobs_closed=all_jobs_closed,
            unsaved_stage_result=result if not published else None)),flush=True)
    except BaseException as exc:
        evidence_error(errors,'stage-progress-write',exc);result['status']='FAILED_NO_AUTOMATIC_RETRY';success=False
    if not success:
        raise EvidenceFailure('STAGE_FAILED_NO_AUTOMATIC_RETRY',primary,errors,result) from primary
