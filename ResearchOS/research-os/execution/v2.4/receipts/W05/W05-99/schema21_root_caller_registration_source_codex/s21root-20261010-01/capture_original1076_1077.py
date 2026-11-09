from pathlib import Path
Q=Path(__file__).resolve().parent
source=(Q/'capture_original1071_1072.py').read_text(encoding='utf-8')
source=source.replace("[(1071,'026f85'),(1072,'728e81')]","[(1076,'93d6d7'),(1077,'e5431b')]")
source=source.replace('original1071-1072.complete-tool-IO.json','original1076-1077.complete-tool-IO.json')
source=source.replace("('read_Task69_basis.py' if ordinal==1071 else 'read_Task69_basis_revision.py')","('run_old21_source_controls.py' if ordinal==1076 else 'run_old21_source_controls_revision.py')")
source=source.replace("old_input_retried=False,counter_reset=False", "retained_attempt_Source_ref=pin(Q/('old21_root.source.initial.py' if ordinal==1076 else 'old21_root.source.numbered0.py')),diagnostic=('Caller numbered SQL parser attempted int(next_v24_sessions.sql) and raised ValueError; Source-control positive failed' if ordinal==1076 else 'Caller first revision treated nonnumbered next_v24_sessions.sql as numbered and rejected exact-schema21 Source'),old_input_retried=False,counter_reset=False")
exec(compile(source,str(Path(__file__)),'exec'),dict(__name__='__main__',__file__=__file__))
