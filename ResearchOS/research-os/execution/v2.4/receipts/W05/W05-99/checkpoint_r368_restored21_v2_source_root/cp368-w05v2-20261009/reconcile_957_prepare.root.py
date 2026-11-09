"""Reconcile known pre-transaction failure957, prepare a new live context and argv."""
import copy
from datetime import datetime,timezone
import json
from pathlib import Path
import sys
import types
N=Path(__file__).resolve().parent
writer=N/'register_cp368.source.py'
m=types.ModuleType('cp368_root_957_reconcile');m.__file__=str(writer);sys.modules[m.__name__]=m
exec(compile(writer.read_bytes(),str(writer),'exec'),m.__dict__)
def main():
    m.require(m.pin(writer)['sha256']=='05079c1be355bd7a55bafaa840b278a0030a681b8aef23cb592ff269b3775d03','EXACT_SOURCE_QUALIFIED_WRITER')
    fr=m.pin(N/'checkpoint.execution.facts.json');m.require(fr['sha256']=='bc3e3da9eb0dd207f6c19e240b162fe7245be7080cb9ebec0befe5a2ea48dca9','EXACT_QUALIFIED_FACTS')
    facts=m.load(fr)
    for ref in facts['canonical_refs']:m.read(ref)
    before=[m.load(ref) for ref in facts['canonical_refs'][:2]]
    origin=m.pin(N/'failure957.original-tool-io.root.json');o=m.load(origin)
    m.require(o['observed_ordinal']==957 and o['actual_outer_exit']==o['actual_python_exit']==1 and o['actual_native_exit'] is None and o['original_result']['exit_code']==1,'ORIGINAL957_EXACT_EXITS')
    output=o['original_result']['output']
    m.require('ValueError: CANONICAL_REF_PATH' in output and 'in read' in output and 'update_pair' not in output,'PRE_TRANSACTION_BOUNDARY')
    m.require(not (N/'source_guard.cleanup.activate.json').exists() and not (N/'canonical_pair.activate.json').exists() and not list(N.glob('activate.transaction.*')),'NO_GUARD_TRANSACTION_OR_WRITES')
    old_ref=m.pin(N/'live-context.postseal.actual.root.json');m.require(old_ref['sha256']=='a0f4ef4aed90fc1221c7e97a392c97ac0735a605902d13e89cdf2732e3c8f353','EXACT_PREFAILURE_LIVE')
    live=m.load(old_ref);m.validate_live(live);m.require(live['next_original_failure_ordinal']==957,'EXACT_OLD_LIVE957')
    live['created_utc']=datetime.now(timezone.utc).isoformat();live['next_original_failure_ordinal']=958
    live['pending'].append(dict(ordinal=957,origin_ref=origin,description='Root actual registration aeafbc rejected noncanonical argv context path before SourceGuard/transaction; outer1/SourcePython1, Native/model NULL. Canon exact-before unchanged. Fresh context and canonical Windows argv are new reconciled inputs.'))
    m.validate_live(live)
    after=m.transform(copy.deepcopy(before[0]),copy.deepcopy(before[1]),facts,fr,before[0],before[1],live)
    m.require(after[0]['work_in_progress']['root_next_failure_ordinal_live']==958 and [v['ordinal'] for v in after[0]['work_in_progress']['later_diagnostics_observed_after_cutoff']]==list(range(953,958)),'NO_LIVE_RESET_AND_ALL_PENDING')
    lr=m.save('live-context.reconciled958.actual.root.json',live);m.read(lr)
    argv=[str(Path(sys.executable).resolve()),'-I','-S','-B','-X','utf8',str(writer.resolve()),'activate',fr['sha256'],str(fr['bytes']),lr['path'],lr['sha256'],str(lr['bytes'])]
    m.require(argv[10]==str(Path(argv[10]).resolve(strict=True)) and argv[10]==lr['path'],'EXACT_WINDOWS_ARGV_CONTEXT_PATH')
    ar=m.save('actual-argv.reconciled958.root.json',dict(argv=argv,cwd=str(m.R),live_context_ref=lr,origin957_ref=origin,canonical_pair_before_refs=facts['canonical_refs'][:2],pre_transaction_failure_reconciled=True,complete_pending=[v['ordinal'] for v in live['pending']],next_original_failure_ordinal=958,actual_executed=False,formal_case_accepted_delta=0))
    print(json.dumps(dict(argv_receipt_ref=ar,live_context_ref=lr,origin957_ref=origin,argv=argv,all_Canon_before_unchanged=True,actual_executed=False),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
