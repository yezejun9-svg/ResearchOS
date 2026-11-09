import sys
sys.dont_write_bytecode=True
import contextlib
import io
import json
from pathlib import Path
import traceback
Q=Path(__file__).resolve().parent
def main():
    source=(Q/'source_controls.py').read_bytes()
    assert source.count(b'source-controls.final.json')==1
    source=source.replace(b'source-controls.final.json',b'source-controls.current-final.json')
    sink=io.StringIO()
    with contextlib.redirect_stdout(sink):
        exec(compile(source,str(Q/'source_controls.py'),'exec'),{'__file__':str(Q/'source_controls.py'),'__name__':'__main__'})
    value=json.loads((Q/'source-controls.current-final.json').read_text(encoding='utf-8'))
    controls=value['controls'];assert len(controls)==22 and all(x['pass'] and x.get('result',True) is not False for x in controls)
    print(json.dumps({'original_controls_passed':22,'caller_actual_source_final':True,
        'actual_registration':False,'future_qualification_ref':None,'Native_Go_SQLite_model':None},ensure_ascii=False))
if __name__=='__main__':
    code=0
    try:main()
    except BaseException:traceback.print_exc();code=1
    print('ROOT_PYTHON_EXIT='+str(code));raise SystemExit(code)
