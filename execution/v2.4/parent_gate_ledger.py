"""Write a derived parent report; authoritative inputs remain read-only.

Command reachability, all-card status and formal evidence validity are separate.
The default output remains execution/v2.4/parent_gate_ledger.json.
"""
from pathlib import Path
import collections
import hashlib
import importlib.util
import json

REPO = Path(__file__).resolve().parents[2]
SPEC = Path('D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4')

def build(repo=REPO, spec=SPEC):
    repo, spec = Path(repo).resolve(), Path(spec).resolve()
    source = repo/'execution/v2.4/formal_case_index.py'
    if not source.resolve().is_relative_to(repo): raise ValueError('formal reader outside repository')
    module_spec = importlib.util.spec_from_file_location('researchos_formal_case_index', source)
    formal = importlib.util.module_from_spec(module_spec)
    reader_raw = source.read_bytes()
    exec(compile(reader_raw,str(source),'exec'),formal.__dict__)
    folder = repo/'execution/v2.4'; plan_path = spec/'contracts/execution.plan.json'
    result = formal.derive_formal_cases(repo, folder/'step_state.json', plan_path)
    def load(path): return formal.strict_json(path.read_bytes())
    plan, state, registry, checkpoint = [load(path) for path in (plan_path,folder/'step_state.json',folder/'commands.json',folder/'checkpoint.json')]
    status = {row['id']:row['status'] for row in state['steps']}
    bindings = load(spec/'contracts/tasks.json')['verification_command_selection']['formal_case_bindings']
    owners = {row['task_id']:row for row in result['owners']}; reachable = set()
    for case in result['cases']:
        selected = [b for b in bindings if b['case_id']==case['case_id']]
        admitted = []
        for binding in selected:
            entry = registry.get('commands',{}).get(binding['key'],{}); selectors = entry.get('selectors',{})
            admitted.append(entry.get('state')=='BOUND' and binding['task_id'] in selectors.get('task_id',[]) and binding['case_id'] in selectors.get('case_id',[]))
        if admitted and all(admitted): reachable.add(case['case_id'])
    parents = collections.OrderedDict()
    for task_id in sorted({step['parent_task'] for step in plan['steps']}):
        cards = sorted(step['id'] for step in plan['steps'] if step['parent_task']==task_id)
        accepted = [card for card in cards if status.get(card)=='ACCEPTED']
        owner = owners.get(task_id,{'owned_case_ids':[],'accepted_case_ids':[],'integrity':'INVALID'})
        cases = owner['owned_case_ids']
        parents[task_id] = {'cards_total':len(cards),'cards_accepted':len(accepted),
            'cards_reported_not_accepted':[card for card in cards if card in status and status[card]!='ACCEPTED'],
            'cards_untracked':[card for card in cards if card not in status], 'all_cards_accepted':bool(cards) and len(accepted)==len(cards),
            'parent_final_status':status.get(task_id+'-99','NOT_STARTED'),'formal_cases':cases,
            'formal_cases_reachable':[case for case in cases if case in reachable], 'formal_cases_unreachable':[case for case in cases if case not in reachable],
            'formal_cases_accepted':owner['accepted_case_ids'],'formal_evidence_integrity':owner['integrity'],'formal_evidence_reasons':owner.get('reasons',[])}
    blocked = sorted((row.get('resource') or row.get('id') or '?') if isinstance(row,dict) else row for row in checkpoint.get('blocked_resources',[]))
    case_ids = [case['case_id'] for case in result['cases']]
    summary = {'generated_by':'execution/v2.4/parent_gate_ledger.py (authority inputs read-only; derived output written)',
        'scope':'DERIVED_REPORT_NOT_ACCEPTANCE_AUTHORITY','registry_revision':registry.get('revision'),
        'cards_accepted':sum(value=='ACCEPTED' for value in status.values()),'cards_total_in_plan':sum(row['cards_total'] for row in parents.values()),
        'parents_total':len(parents),'parents_with_every_card_accepted':[task for task,row in parents.items() if row['all_cards_accepted']],
        'accepted_parent_final_ids':[task+'-99' for task,row in parents.items() if row['parent_final_status']=='ACCEPTED'],
        'formal_cases_total':result['required_formal_cases'],'formal_cases_reachable_by_a_selector':sorted(reachable),
        'formal_cases_unreachable':[case for case in case_ids if case not in reachable],
        'formal_cases_accepted':result['accepted_case_ids'],'formal_case_accepted_count':result['formal_cases_accepted'],
        'formal_evidence_integrity':result['integrity'],'formal_evidence_reasons':result['reasons'],'formal_case_states':result['cases'],
        'formal_dependency_snapshot':result['dependency_snapshot'],'blocked_resources':blocked,
        'reading':'Reachability is diagnostic. Formal cases require exact final ownership, independent full evidence and current applicable inputs registered on canonical accepted owner-99 rows.',
        'parents':parents}
    checked = formal.recheck_inputs(result['dependency_snapshot'])
    if checked['status']!='PASS': raise ValueError('formal evidence changed before report: '+checked['reason'])
    if hashlib.sha256(source.read_bytes()).digest()!=hashlib.sha256(reader_raw).digest(): raise ValueError('formal reader changed before report')
    return summary

def main():
    summary = build()
    (REPO/'execution/v2.4/parent_gate_ledger.json').write_text(json.dumps(summary,ensure_ascii=False,indent=1)+'\n',encoding='utf8')
    keys = ('registry_revision','cards_accepted','cards_total_in_plan','parents_total','parents_with_every_card_accepted','formal_cases_total','formal_case_accepted_count','formal_evidence_integrity')
    print(json.dumps({key:summary[key] for key in keys},indent=1,ensure_ascii=False))
    print('reachable cases:',len(summary['formal_cases_reachable_by_a_selector']),'| unreachable:',len(summary['formal_cases_unreachable']))
    print('blocked resources:',summary['blocked_resources'])
    for task,row in sorted(summary['parents'].items(),key=lambda item:item[1]['cards_accepted']-item[1]['cards_total'])[:6]:
        print('%s cards %d/%d | reported-not-accepted %s | cases %d, unreachable %d' % (task,row['cards_accepted'],row['cards_total'],row['cards_reported_not_accepted'],len(row['formal_cases']),len(row['formal_cases_unreachable'])))

if __name__=='__main__': main()
