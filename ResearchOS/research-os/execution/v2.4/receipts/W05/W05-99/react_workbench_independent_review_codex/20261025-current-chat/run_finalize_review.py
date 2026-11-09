from review_driver import *
run('029-finalize',[PY,'-B','-X','utf8',str(E/'finalize_review.py')])
print((E/'commands/029-finalize/stdout.bin').read_text())
