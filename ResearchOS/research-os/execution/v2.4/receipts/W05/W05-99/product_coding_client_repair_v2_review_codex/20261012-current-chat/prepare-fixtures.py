from pathlib import Path
O=Path(__file__).resolve().parent
old=O.parents[1]/'product_coding_client_review_codex/20261012-current-chat'
s=(old/'fixture.mjs').read_text()
s=s.replace("path.join(root,'.local/worktrees/w05-product-coding-client-20261012/.local/coding-client-bound-final3')","'C:/Users/yqyyds/.codex/researchos-build-worktrees/coding-client-v2-20261012/.local/builds/product-coding-client-repair-v2-20261012'")
s=s.replace("modelRef:'model-1',coding:coding()","modelRef:'model-1',model:null,coding:coding()")
(O/'fixture.mjs').write_text(s,encoding='utf-8')

