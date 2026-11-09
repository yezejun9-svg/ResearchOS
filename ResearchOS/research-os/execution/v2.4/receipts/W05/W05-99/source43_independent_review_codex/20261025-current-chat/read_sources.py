import sys,pathlib,json,hashlib
sys.stdout.reconfigure(encoding='utf-8')
for item in sys.argv[1:]:
    path,sep,span=item.partition('::')
    print('\nFILE '+path)
    lines=pathlib.Path(path).read_text(encoding='utf-8-sig').splitlines()
    start,end=(map(int,span.split('-')) if sep else (1,len(lines)))
    for num,line in enumerate(lines,1):
        if start<=num<=end:print(f'{num}: {line}')
