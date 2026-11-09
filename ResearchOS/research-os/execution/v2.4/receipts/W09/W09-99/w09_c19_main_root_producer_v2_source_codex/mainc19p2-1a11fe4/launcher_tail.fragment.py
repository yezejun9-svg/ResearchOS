    except BaseException as exc:primary=exc;error=repr(exc)
    finally:
        try:runner.uuid=original_uuid
        except BaseException as exc:m.evidence_error(cleanup_errors,'launcher-uuid-restore',exc)
        try:m.require(uuid.uuid4 is stdlib_uuid4 and runner.uuid is original_uuid,'UUID_MODULE_RESTORED_UNMODIFIED')
        except BaseException as exc:m.evidence_error(cleanup_errors,'launcher-uuid-observation',exc)
        launcher_ref=None;consumed=None
        try:launcher_ref=m.pin(__file__)
        except BaseException as exc:m.evidence_error(cleanup_errors,'launcher-source-pin',exc)
        try:consumed=object.__getattribute__(provider,'_used')
        except BaseException as exc:m.evidence_error(cleanup_errors,'launcher-uuid-consumed',exc)
        observation=dict(permit_ref=permit_ref,runner_ref=runner_ref,launcher_ref=launcher_ref,
            runner_returned_exit=returned,error=error,one_uuid_consumed=consumed,cleanup_errors=cleanup_errors,
            stdlib_uuid_modified=False,Main_source_modified=False,unknown_individual_descendant_exit=None)
        try:m.save(root,'launcher.closed.json',observation)
        except BaseException as exc:m.evidence_error(cleanup_errors,'launcher-closed-save',exc)
    if primary is not None or cleanup_errors:
        raise m.EvidenceFailure('LAUNCHER_FAILED_NO_AUTOMATIC_RETRY',primary,cleanup_errors,observation) from primary
    return returned
