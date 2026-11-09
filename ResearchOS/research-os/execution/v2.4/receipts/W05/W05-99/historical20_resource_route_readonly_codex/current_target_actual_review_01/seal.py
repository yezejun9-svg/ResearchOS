import sys
sys.dont_write_bytecode=True
import json,hashlib,datetime
from pathlib import Path
O=Path(__file__).resolve().parent
def pin(p):
 p=Path(p).resolve();b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def read(p):return json.loads(Path(p).read_bytes())
def save(n,o):
 with (O/n).open('xb') as f:f.write((json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(O/n)
g=read(O/'sourceguard.close.json');assert g['closed'] and not g['errors'] and g['retained_handles_count']==0
identity=read(O/'final-identity-head-check.json');assert identity['identity_unchanged']
h={'schema':'researchos.readonly-historical20-resource-route.v1','status':'READONLY_RESOURCE_ROUTE_AND_PRODUCT_IMPLEMENTATION_GAP_IDENTIFIED','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'commit':'3225a31fd25969c6a5e071a2fc686cb4a835e162','tree':'955430efd12ef450a0eeb86a5f07054518c0e058','report':pin(O/'report.md'),'inventory':pin(O/'resource-inventory.json'),'full_git_tree_raw':pin(O/'git-raw/full-tree.stdout.raw'),'historical_source_pins':pin(O/'historical-source.pins.json'),'supplemental_source_pins':pin(O/'supplemental-source.pins.json'),'current_source_pins':pin(O/'current-source.pins.json'),'source_excerpts':pin(O/'source-excerpts.json'),'module_resource_presence':pin(O/'expanded-module-resource-presence.json'),'guard_closed':pin(O/'sourceguard.close.json'),'identity_head_unchanged':pin(O/'final-identity-head-check.json'),'historical_source_available':True,'historical_program_built':False,'historical_control_installs_old_session_DDL':False,'LEG2_is_historical_CLI_generated_DB':False,'current_20_to21_production_upgrade_entry_exists':False,'native_original_root_grant_fixed23_to24':True,'next_root_action':'Freeze dedicated schema20-to21 Source contract and reachable production upgrade path, distinguishing historical CLI base schema from LEG2 synthetic old-session extension; separately resource-build historical control/backup only under Root authorization.','product_acceptance':False,'formal_acceptance':False,'Go_compiler_test_product_SQL_native_model_executed':False,'private_keys_or_original_trial_read':False,'Main_canonical_Source_modified':False,'review_errors':[pin(O/'failure-origin.888.json')],'counter_reset':False,'STOP':True}
save('HDF.json',h)
ex={'MF.json','postseal.json','seal.original-tool-io.json'};members=[pin(p) for p in sorted(O.rglob('*')) if p.is_file() and not(p.parent==O and p.name in ex)]
mf=save('MF.json',{'members':members,'root_exclusions':sorted(ex),'authority':'READONLY_RESOURCE_ANALYSIS_ONLY'})
for v in members:assert pin(v['path'])==v
post=save('postseal.json',{'status':'PASS','manifest':mf,'handoff':pin(O/'HDF.json'),'member_count':len(members),'all_exact_sha256_bytes':True,'formal_acceptance':False})
print(json.dumps({'HDF':pin(O/'HDF.json'),'MF':mf,'postseal':post,'failure888':pin(O/'failure-origin.888.json')},ensure_ascii=False))
