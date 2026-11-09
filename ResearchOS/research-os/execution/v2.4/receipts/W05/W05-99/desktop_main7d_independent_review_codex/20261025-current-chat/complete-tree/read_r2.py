import pathlib,sys
E=pathlib.Path(__file__).parent
for spec in sys.argv[1:]:
 name,start,end=spec.rsplit(':',2);lines=(E/'source-r2'/name).read_text(encoding='utf-8').splitlines();print(name)
 for i in range(int(start)-1,min(int(end),len(lines))):print(f'{i+1}: {lines[i]}')
