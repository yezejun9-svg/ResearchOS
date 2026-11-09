import json
from pathlib import Path
Q=Path(__file__).resolve().parent
BASE=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/schema21_root_caller_registration_source_codex/s21root-20261010-02")
h=json.loads((BASE/'HDF.json').read_bytes());original=Path(h['base_Source_hdf_ref']['path']).parent
source=(original/'prepare_Source_audit_toolpairs.py').read_text(encoding='utf-8').replace("'task69_'", "'task79_'")
exec(compile(source,str(Path(__file__)),'exec'),dict(__name__='__main__',__file__=__file__))
