from pathlib import Path
import json,hashlib,datetime,shutil
NS=Path(__file__).resolve().parent
def load(name):return json.loads((NS/name).read_bytes())
def save(name,value):(NS/name).write_text(json.dumps(value,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
def ref(name):
    p=NS/name; b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
draft=NS/'draft_before_final_verification'
draft.mkdir()
for name in ['source_review.json','handoff.json','outer_tool_invocations.json']:
    shutil.copyfile(NS/name,draft/name)
failure=load('failure_origins.json')
assert failure['actual_outer_nonzero_count']==1 and failure['origins'][0]['chunk_id']=='fe789d'
frozen=load('frozen-source-verification.json')
assert frozen['all_match'] and frozen['source_refs_checked']==153 and frozen['git_blob_checks']==137
ledger=load('outer_tool_invocations.json')
ledger['actuals'] += [
 {'chunk_id':'f08e43','actual_exit':0,'operation':'Write owned initial review records','argv':['python',str(NS/'write_review_records.py')]},
 {'chunk_id':'b36be9','actual_exit':0,'operation':'Inspect public before-vector actual schema','output_basis':'Observed native tool transcript'},
 {'chunk_id':'fe789d','actual_exit':1,'operation':'First additional frozen-source verification','argv':['python',str(NS/'verify_frozen_sources.py')],'failure_origin':'f08-whole-review-frozen-vector-shape-fe789d','failed_script_sha256':'94fd79be025b5e6bd0b591cf27c452381fb35554b72f6a161bcf768f32e0dd8f'},
 {'chunk_id':'909f91','actual_exit':0,'operation':'Inspect actual before nested vs after flattened record schemas; diagnose projection correction','output_basis':'Observed native tool transcript'},
 {'chunk_id':'01b18e','actual_exit':0,'operation':'Distinct attempt2 explicit original metadata projection; all153 current sources and137 pinned Git blobs checked','argv':['python',str(NS/'attempt2/verify_frozen_sources.py')],'session_id':31153,'terminal_chunk_id':'e2eeeb','outer_exit_basis':'Initial exec yielded31153; write_stdin e2eeeb returned actual0'},
]
ledger['native_git_source_checks']=137
ledger['failure_origins_preserved']=True
save('outer_tool_invocations.json',ledger)
review=load('source_review.json')
review['independent_frozen_source_checks']={'refs':153,'pinned_Main_Git_blobs':137,'all_match':True,'receipt':'frozen-source-verification.json'}
review['reviewer_actual_tool_failures']=1
review['reviewer_failure_origin']='f08-whole-review-frozen-vector-shape-fe789d'
review['failed_driver_retained']='verify_frozen_sources.py'
review['distinct_corrected_driver']='attempt2/verify_frozen_sources.py'
review['failure_counter_canonical_import']='Root pending; no child canonical writes/reset'
review['refs'].append('frozen-source-verification.json')
save('source_review.json',review)
md=(NS/'REVIEW.md').read_text(encoding='utf-8')
md=md.replace('153 个公开源快照保存到本审查目录。','153 个公开源快照保存到本审查目录；所有 153 条 original 源引用重新核验一致，其中 137 个产品/依赖声明/SQL 快照与固定 Main Git blob 逐字节一致。')
md += '\n复核工具记录另有一次实际 exit1：初次补验把 nested before 与 flat after 元数据直接比较，未进入源/SQL/Git 检查。保留失败脚本及 `fe789d` 来源，另开明确 original 投影的 attempt2，153/137 核验实际 exit0。此工具失败需 Root 单独累计；不归产品 case，也未重置历史失败。\n'
(NS/'REVIEW.md').write_text(md,encoding='utf-8')
proposal_lines=(NS/'inputs/proposal-1.json').read_text(encoding='utf-8').splitlines()
markers={'C01':'"unfinished_contract"','C02':'"new24_dispatch_origin_guard"','C03':'"binding_shape"','I01':'"limits_are_new_policy"','I02':'"minimal_counts"'}
findings=[]
for key,needle in markers.items():
    line=next(i+1 for i,x in enumerate(proposal_lines) if needle in x)
    findings.append({'id':key,'severity':'Critical' if key.startswith('C') else 'Important','input':'inputs/proposal-1.json','line':line,'key':needle,'fix_details':'REVIEW.md and required_closed_contract.json'})
save('findings.json',{'verdict':'REQUEST_CHANGES','findings':findings,'all_19_paths_reviewed_as_design':True,'implementation_acceptance':False})
handoff=load('handoff.json')
handoff['review']=ref('source_review.json')
handoff['required_closed_contract']=ref('required_closed_contract.json')
handoff['minimal_verification']=ref('minimal_verification.json')
handoff['failure_origins']=ref('failure_origins.json')
handoff['frozen_sources']=ref('frozen-source-verification.json')
handoff['raw_tool_failure_count']=1
handoff['successful_distinct_attempt2_terminal_chunk']='e2eeeb'
handoff['manifest_self_excluded']=True
save('handoff.json',handoff)
files=[]
for p in sorted(NS.rglob('*')):
    if p.is_file() and p.name!='manifest.json':
        b=p.read_bytes(); files.append({'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)})
save('manifest.json',{'schema':'researchos.independent-review.manifest.v1','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'count':len(files),'files':files,'self_excluded':True,'public_source_receipts_only':True,'product_SQL_canonical_writes':0,'test_compile_calls':0,'review_verdict':'REQUEST_CHANGES','actual_tool_nonzero_retained':1})
print(json.dumps({'namespace':str(NS),'file_count':len(files),'review':ref('source_review.json'),'handoff':ref('handoff.json'),'manifest':ref('manifest.json'),'failure_origins':ref('failure_origins.json'),'required_closed_contract':ref('required_closed_contract.json')},ensure_ascii=True))
