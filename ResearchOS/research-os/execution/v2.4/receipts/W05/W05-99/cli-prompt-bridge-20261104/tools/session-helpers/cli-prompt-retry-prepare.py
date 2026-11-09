from pathlib import Path
here=Path(__file__).parent
s=(here/'cli-prompt-test-controller.py').read_text(encoding='utf-8')
s=s.replace("run=OUT/'checks-01'","run=OUT/'checks-02'")
s=s.replace("'attempt_index':1", "'attempt_index':2,'failure_origin':'cli-prompt-sparse-module-closure-20261104','previous_attempt':'checks-01'")
s=s.replace("['cli-prompt-author.py','cli-prompt-tests-author.py','cli-prompt-metadata.py','cli-prompt-test-controller.py']", "['cli-prompt-author.py','cli-prompt-tests-author.py','cli-prompt-metadata.py','cli-prompt-pretest.py','cli-prompt-int64-fix.py','cli-prompt-retry-prepare.py','cli-prompt-test-controller.py','cli-prompt-test-controller-r2.py']")
(here/'cli-prompt-test-controller-r2.py').write_text(s,encoding='utf-8',newline='\n')
print('checks02 same resource-origin retry prepared; checks01 unchanged')
