import pathlib

here = pathlib.Path(__file__).resolve().parent
target = pathlib.Path(r'D:\作品集\ResearchOS\research-os\.local\worktrees\source43-b-stop-finalpath-20261015')
listing = (here / '004-worktree-list' / 'stdout.raw').read_text(encoding='utf-8')
assert not target.exists(), 'target worktree path already exists'
assert str(target).replace('\\', '/') not in listing, 'target worktree already registered'
assert 'refs/heads/source43-b-stop-finalpath-20261015' not in listing, 'target branch already registered'
print('TARGET_ABSENT', target)
