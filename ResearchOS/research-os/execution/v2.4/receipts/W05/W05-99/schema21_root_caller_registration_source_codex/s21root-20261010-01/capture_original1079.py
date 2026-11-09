from pathlib import Path
Q=Path(__file__).resolve().parent
source=(Q/'capture_original1071_1072.py').read_text(encoding='utf-8')
source=source.replace("[(1071,'026f85'),(1072,'728e81')]","[(1079,'7cb837')]")
source=source.replace('original1071-1072.complete-tool-IO.json','original1079.complete-tool-IO.json')
source=source.replace('actual_outer_exit=1,actual_python_exit=1','actual_outer_exit=0,actual_python_exit=None')
source=source.replace("failed_script_ref=pin(Q/('read_Task69_basis.py' if ordinal==1071 else 'read_Task69_basis_revision.py'))","failed_script_ref=None,diagnostic='PowerShell nonterminating InvalidOperation on null-valued contract field .GetType(); successful other output retained; outer0 does not imply inner success',actual_inner_process_exit=None")
exec(compile(source,str(Path(__file__)),'exec'),dict(__name__='__main__',__file__=__file__))
