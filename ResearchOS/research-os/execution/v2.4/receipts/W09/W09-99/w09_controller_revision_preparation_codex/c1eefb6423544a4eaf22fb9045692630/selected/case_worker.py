"""Future case wrapper child; 120s test / cleanup5 / enclosing ownedJob150. Unexecuted."""
import sys
sys.dont_write_bytecode=True
import argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from controller_common import *
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--request',required=True);ap.add_argument('--sha256',required=True);a=ap.parse_args()
 pin=file_ref(a.request)
 if pin['sha256']!=a.sha256:raise Stop('Case request changed')
 r=raw_json(Path(a.request).read_bytes())
 if r['schema']!='researchos.w09.owned-case-request.v1' or r['authorized_by_controller'] is not True or r['source_commit']!=CANDIDATE:raise Stop('Case authority missing')
 g,s,out=validate_grant(r['root_grant_ref']['path'],r['root_grant_ref']['sha256'])
 if r['spec_ref']!=g['spec_ref'] or r['self_ref']!=s['case_worker_ref'] or r['debug_helper_ref']!=s['debug_helper_ref'] or r['python_ref']!=g['tools']['python']:raise Stop('Worker mechanism substitution')
 if not no_alias(r['output_dir']).is_relative_to(out/'native'):raise Stop('Case output outside authorized run')
 verify(r['self_ref']);verify(r['debug_helper_ref'])
 if str(Path(__file__).resolve())!=r['self_ref']['path']:raise Stop('Worker identity')
 if not sys.flags.isolated or not sys.flags.no_site or sys._xoptions.get('utf8') is not True:raise Stop('Required interpreter flags')
 verify(r['python_ref'])
 if str(Path(sys.executable).resolve())!=r['python_ref']['path']:raise Stop('Interpreter identity')
 if r['timeout']!=120 or r['process_cap'] not in (1,2):raise Stop('Case cap')
 for image in r['images']:verify(image)
 debug=trusted_module(r['debug_helper_ref']['path'],r['debug_helper_ref'])
 output=no_alias(r['output_dir'])
 with (output/'stdout.raw').open('xb') as so,(output/'stderr.raw').open('xb') as se:
  result=debug.run_owned(r['argv'],r['cwd'],r['env'],so,se,120,r['expected_image'],r['images'],r['allowed_module_files'],r['process_cap'],creation_flags=0x08000000)
 write_json(output/'case-owned.json',result)
 require_job(result,True)
if __name__=='__main__':main()
