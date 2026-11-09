import pathlib

d = pathlib.Path(r'D:\作品集\ResearchOS\research-os\.local\source43-b-stop-finalpath-20261015-tmp')
c = pathlib.Path(r'C:\Users\yqyyds\.codex\researchos-fixture-cache\source43-b-stop-finalpath-20261015')
for path in [d, d / 'tmp', d / 'gotmp', d / 'gocache', c]:
    path.mkdir(parents=True, exist_ok=True)
    print('READY', path.resolve())
