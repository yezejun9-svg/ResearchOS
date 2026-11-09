import argparse,os,sys
import reviewer_logger
p=argparse.ArgumentParser();p.add_argument('--label');p.add_argument('--cwd');p.add_argument('--env',action='append',default=[]);p.add_argument('command',nargs=argparse.REMAINDER)
a=p.parse_args()
if a.cwd:os.chdir(a.cwd)
for pair in a.env:
    k,v=pair.split('=',1);os.environ[k]=v
sys.argv=[sys.argv[0]]+(a.command[1:] if a.command[0]=='--' else a.command)
reviewer_logger.main()
