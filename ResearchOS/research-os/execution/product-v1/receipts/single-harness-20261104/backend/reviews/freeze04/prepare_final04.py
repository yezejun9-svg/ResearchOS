from pathlib import Path
root=Path(__file__).resolve().parent
p=root/'qa_final04.py'
assert not p.exists()
s=(root/'qa_final.py').read_text(encoding='utf-8')
s=s.replace("RUN=HERE/'run-03'", "RUN=HERE/'run-04'")
s=s.replace('final-03','final-04').replace('diagnostics-03','diagnostics-04')
s=s.replace('e1b64dc538c0a89ef622bf000459657b728aa77d0cada514c37c4845eb45b541','ecc1e5574588d9de6ac450259eb363e5e2bea1fb1b7e716e3e9014c0ca287572')
s=s.replace('92c498512a18902714507579f8b0926d6080023ff6aff40cd45c35aad8220663','712fa19353787bd4357d52179f931972c14a3a60a60346b737cc92d3f60f1167')
s=s.replace('45ba15bd6705d358dccab4baa1608d0043510befce223897d775096680001905','85db44d9b933bb760c4f05c73f6a4f2989573ac6708b5d55a73182fc1f8e3d35')
s=s.replace('ac9f013d5ecb42705ded60ae36bb82af85058bb8d74ffa93d710db4200f74c00','31fca56d81984a1eeba0baeabd2789b2cef08f173b190550c89e46039415ed09')
s=s.replace("'internal/api/independent_harness_transport_test.go':'independent_api_test.go'", "'internal/api/independent_harness_transport_test.go':'independent_api_test.go',\n        'internal/domain/independent_unknown_atomic_test.go':'independent_atomic_test.go'")
s=s.replace("save(phase+'.command.json',", "controller_copy=RUN/(phase+'.controller.py.txt'); assert not controller_copy.exists(); controller_copy.write_bytes(Path(__file__).read_bytes())\n save(phase+'.command.json',")
s=s.replace("[('-overlay='+str(RUN/'overlay-atomic.json')) if arg.startswith('-overlay=') else arg for arg in common]", "common")
p.write_text(s,encoding='utf-8')
print(str(p))
