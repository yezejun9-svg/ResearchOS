from pathlib import Path
import sys,traceback
Q=Path(__file__).resolve().parent
def main():
    text=(Q/'seal_original1168.py').read_text(encoding='utf-8')
    for before,after in [('original1168','original1172'),('784193','993be3'),('nf5actual_review_v5_actual_run_in','nf5actual_review_v7_actual_run_in'),('review_actual_nf5.v5.py','review_actual_nf5.v7.py'),('actual-review-v5-guard.closed.json','actual-review-v7-guard.closed.json'),('guard_entries=3558','guard_entries=3564'),('EXACT_ONE_ACTUAL_HOST_RESULT','SAME_PREPARE_HOST_SESSION'),('G01 review_group root_prepare_pair after prior native/owned/business/3905/19 checks','G01 prefix reused from original1168; new Rootprepare session binding rejects batch session variable before Mode/launcher checks')]:
        assert before in text; text=text.replace(before,after)
    with(Q/'seal_original1172.py').open('xb')as f:f.write(text.encode('utf-8'))
    return 0
if __name__=='__main__':
    rc=1
    try:rc=main()
    except BaseException:traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(rc));sys.exit(rc)
