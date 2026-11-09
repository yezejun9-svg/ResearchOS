import hashlib,json,sys,traceback
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W09/W09-99';Q=Path(__file__).resolve().parent
P=B/'full_w09_main_native_producer_source_codex/fullw09-20261010-06';S=B/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
def pin(p):
    raw=Path(p).read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def doc(p):return json.loads(Path(p).read_bytes())
def main():
    choice=doc(P/'source.choice.json');rows={};overview={}
    for key,label in [('W09-G01','G01'),('W09-G02','G02')]:
        root=Path(choice['selectors'][key]['receipt_root'])
        row=dict(prepare_ref=pin(root/'prepare.ready.json'),producer_closed_ref=pin(root/'producer/validation.closed.json'))
        for field,stage in [('prepare_initial_Root_capture_ref','prepare-initial'),('prepare_completed_Root_capture_ref','prepare-completed'),('run_initial_Root_capture_ref','run-initial'),('run_completed_Root_capture_ref','run-completed')]:row[field]=pin(S/('nf6-'+label+'-'+stage+'.host-pair.root.json'))
        rows[key]=row;ready=doc(row['prepare_ref']['path']);closed=doc(row['producer_closed_ref']['path'])
        captures={}
        for field in list(row)[2:]:
            binding=doc(row[field]['path']);raw=Path(binding['original_capture_ref']['path']).read_bytes();capture=[json.loads(x)for x in raw.splitlines()]
            captures[field]=dict(binding=binding,call_payload=capture[1]['payload'],output_payload_type=type(capture[2]['payload'].get('output')).__name__)
        overview[key]=dict(ready_keys=list(ready),closed_keys=list(closed),status=[ready['status'],closed['status']],request_ref=closed['request_ref'],environment=ready['environment'],summary=closed['summary'],invocations=[dict(label=x['label'],ref=x['ref'])for x in closed['invocation_observations']],guard_labels=[x['label']for x in closed['guard_cleanups']],captures=captures)
    for name,value in [('partial-input-observed.json',dict(schema='researchos.w09-nf6-two-closed-partial-review-input.v1',source_review_ref=pin(B/'full_w09_nf6_independent_source_review_codex/review-20261010-01/decision.json'),groups=rows)),('partial-basis-shapes.json',overview)]:
        with (Q/name).open('xb')as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    print(json.dumps(dict(input_ref=pin(Q/'partial-input-observed.json'),shape_ref=pin(Q/'partial-basis-shapes.json'),shapes=overview),ensure_ascii=False))
    return 0
if __name__=='__main__':
    rc=1
    try:rc=main()
    except BaseException:traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(rc));sys.exit(rc)
