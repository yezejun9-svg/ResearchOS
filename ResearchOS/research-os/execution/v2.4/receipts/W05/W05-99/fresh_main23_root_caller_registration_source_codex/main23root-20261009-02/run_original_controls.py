import sys
sys.dont_write_bytecode=True
import contextlib
import io
import json
from pathlib import Path
import runpy
import traceback

Q=Path(__file__).resolve().parent
if __name__=='__main__':
    code=0
    try:
        output=io.StringIO()
        with contextlib.redirect_stdout(output):runpy.run_path(str(Q/'source_controls.py'),run_name='source_controls_only')
        value=json.loads(output.getvalue())
        assert len(value['controls'])==22 and all(row['pass'] and row.get('result',True) is not False for row in value['controls'])
        print(json.dumps({'scope':'SOURCE_SYNTHETIC_NONAUTHORITATIVE','original_controls_passed':22,'canonical_before_equal_after':value['canonical_before']==value['canonical_after'],'current_revisions':value['current_revisions'],'actual_registration':False,'actual_future_qualification_ref':None,'Native_Go_SQLite_model':None},ensure_ascii=False))
    except BaseException:traceback.print_exc();code=1
    print('ROOT_PYTHON_EXIT='+str(code));raise SystemExit(code)
