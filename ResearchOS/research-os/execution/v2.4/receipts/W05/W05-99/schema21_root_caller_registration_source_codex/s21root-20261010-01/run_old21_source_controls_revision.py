from pathlib import Path
Q=Path(__file__).resolve().parent
source=(Q/'run_old21_source_controls.py').read_text(encoding='utf-8')
source=source.replace("(Q/'exact-inverse.json')", "(Q/'numbered-SQL-revision.inverse.json')")
exec(compile(source,str(Path(__file__)),'exec'),dict(__name__='__main__',__file__=__file__))
