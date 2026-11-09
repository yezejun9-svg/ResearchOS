from pathlib import Path
import json,ast,difflib
own=Path(r'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/native_private_stdin_helper_revision_codex/320740c9ef7c4dbaa6cae48633aa8e60');prior=own.parent.parent/'native_private_stdin_helper_source_codex/d6e8f35ea16d42c9b7f30c91faec090d'
contract=(prior/'CONTRACT.md').read_text(encoding='utf-8')
oldparagraph='The helper requests a 65536-byte anonymous pipe, validates both ends as FILE_TYPE_PIPE, performs one bounded <=4096-byte WriteFile, clears the buffer, and closes the writer before child creation. This is a synchronous preload into an empty pipe; the requested pipe buffer is larger than the maximum payload. Root must prove 4096-byte completion and EOF on the actual Windows host before credential use.'
newparagraph='Each invocation requests an anonymous pipe, validates both ends as FILE_TYPE_PIPE, then queries GetNamedPipeInfo on the read handle. It selects inbound capacity for a server-end reader and outbound capacity for a client-end reader, rejects message/unknown type, zero capacity or capacity below the bounded input, and uses PeekNamedPipe to require an empty pipe. Both original handles are non-inherited, exclusive and unpublished at this point. Only then does it perform its sole <=4096-byte WriteFile, with preparation-deadline checks immediately before and after. It clears the buffer and closes the writer before child creation. The requested 65536 size is treated only as a suggestion. Root must independently review these per-invocation checks and run the dummy native matrix before real credential use.'
assert contract.count(oldparagraph)==1;contract=contract.replace(oldparagraph,newparagraph,1)
contract=contract.replace('preserve the pinned original implementation byte for byte, apart from unconditional private-buffer clearing in finally.','preserve the pinned original implementation after normalizing line endings, apart from unconditional private-buffer clearing in finally. Raw line-ending equality is not claimed.')
contract=contract.replace(chr(96)+'root_verify_private_pipe.py <fresh-absolute-output-directory>'+chr(96),chr(96)+'python -I -S -B -X utf8 root_verify_private_pipe.py <fresh-absolute-output-directory>'+chr(96))
contract+='\n## Capacity review sources\n\n[CreatePipe](https://learn.microsoft.com/en-us/windows/win32/api/namedpipeapi/nf-namedpipeapi-createpipe) defines suggested buffer sizing and behavior when a synchronous write fills the pipe. [GetNamedPipeInfo](https://learn.microsoft.com/en-us/windows/win32/api/namedpipeapi/nf-namedpipeapi-getnamedpipeinfo) supplies end/type flags and buffer sizes, including for anonymous pipes. [PeekNamedPipe](https://learn.microsoft.com/en-us/windows/win32/api/namedpipeapi/nf-namedpipeapi-peeknamedpipe) supplies available-byte count without consuming input. This revision preserves the prior process, Job, inheritance and cleanup suffix after normalizing line endings.\n'
contract+='\nThe dummy child uses fixed Python flags -I -S -B -X utf8 so site/user startup and bytecode cache writes do not enter the probe. The capacity finding is a source-level boundedness gap; no host hang was reproduced by the Source author or claimed here.\n'
(own/'CONTRACT.md').write_text(contract,encoding='utf-8')
e=json.loads((own/'static-evidence.json').read_bytes())
e.pop('prior_process_lifecycle_suffix_exact',None)
e['prior_process_lifecycle_suffix_equal_after_line_ending_normalization']=True
e['raw_lifecycle_suffix_byte_equality_claimed']=False
e['public_probe_child_fixed_python_flags']=['-I','-S','-B','-X','utf8']
tail=b'        size = SIZE_T()\n        initialize_attrs(None, 1, 0, ctypes.byref(size))'
a=(prior/'windows_owned_private_stdin.py').read_bytes();c=(own/'windows_owned_private_stdin.py').read_bytes()
an=a.replace(b'\r\n',b'\n');cn=c.replace(b'\r\n',b'\n')
assert an[an.index(tail):]==cn[cn.index(tail):]
e['raw_line_ending_counts']={'prior':{'CRLF':a.count(b'\r\n'),'LF':a.count(b'\n')},'revision':{'CRLF':c.count(b'\r\n'),'LF':c.count(b'\n')}}
(own/'static-evidence.json').write_text(json.dumps(e,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
patch=''
for name in ['windows_owned_private_stdin.py','root_verify_private_pipe.py','CONTRACT.md']:
 patch+=''.join(difflib.unified_diff((prior/name).read_text(encoding='utf-8').splitlines(True),(own/name).read_text(encoding='utf-8').splitlines(True),fromfile=str(prior/name),tofile=str(own/name)))
(own/'revision.patch').write_text(patch,encoding='utf-8')
for name in ['windows_owned_private_stdin.py','private_pipe_public_probe.py','root_verify_private_pipe.py']:ast.parse((own/name).read_text(encoding='utf-8'),filename=name)
assert (own/'CONTRACT.md').read_text(encoding='utf-8')==contract
print(json.dumps(e,ensure_ascii=True))

