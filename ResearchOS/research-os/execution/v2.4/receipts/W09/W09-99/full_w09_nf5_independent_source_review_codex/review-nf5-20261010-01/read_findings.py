import json,sys,traceback
from pathlib import Path
def main():
    q=Path(__file__).resolve().parent
    d=json.loads((q/'finite-review.json').read_bytes())
    print(json.dumps([x for x in d['checks']if not x['passed']],ensure_ascii=False));return 0
if __name__=='__main__':
    rc=1
    try:rc=main()
    except BaseException:traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(rc));sys.exit(rc)
