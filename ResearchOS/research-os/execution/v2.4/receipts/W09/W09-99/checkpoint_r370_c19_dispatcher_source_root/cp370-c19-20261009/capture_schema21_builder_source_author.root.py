"""Reuse the bounded actual-author capture with exact old21 Source pins."""
from pathlib import Path
N=Path(__file__).resolve().parent
p=N/'capture_main23_v4_source_author.root.py'
source=p.read_text(encoding='utf-8')
substitutions={
    "actor='/root/backup_regression_resources'":"actor='/root/native_temp_independent_review'",
    '348034a2f2f23342f6a309ed14ffe64183a3bbb031ed79d6c8ed5facf34c0fd3':'355407c30d1d0081a5fac90d32e8c7c47f95ddb0d56681768d8688bf2684ef84',
    'dd65dabdff33ccc10b229222992cf7db5702837c60cd7ed565769248c09e88c1':'6e40bbe378edf370ac8cb870f581d76cd8b48b3c127534855068787c66188069',
    'main23.v4.peer.source-author':'schema21.builder.peer.source-author',
}
for old,new in substitutions.items():
    assert source.count(old) >= 1
    source=source.replace(old,new)
exec(compile(source,str(p),'exec'),globals())
