import pathlib,sys
B=pathlib.Path(__file__).parent/'C51-r3-r4-static-snapshot'
for spec in sys.argv[1:]:
    path,_,span=spec.partition(':')
    lines=(B/path).read_text(encoding='utf-8').splitlines()
    print('\nFILE '+path)
    start,end=map(int,span.split('-')) if span else (1,len(lines))
    for n in range(start,min(end,len(lines))+1): print(f'{n}: {lines[n-1]}')
