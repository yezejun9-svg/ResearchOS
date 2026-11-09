// Existing registration/management fixtures, in one Node process with live IO
// poisoned. Their temporary files stay under this author's fresh TEMP/TMP.
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
const require=createRequire(import.meta.url);
for(const [name,keys] of [['node:child_process',['spawn','execFile','execFileSync','execSync']],
  ['node:http',['request','get','createServer']],['node:net',['connect','createConnection','createServer']]]) {
  for(const key of keys) require(name)[key]=()=>{throw Error('REAL_IO_FORBIDDEN_BY_AUTHOR_SCOPE');};
}
process.env.RESEARCHOS_NATIVE_CREATE_PILOT='0';
const root='D:/作品集/ResearchOS/research-os/.local/worktrees/w14-native-create-clients-20261104/tests/ui/desktop/';
await import(pathToFileURL(root+'coding-authorization-boundary.test.mjs').href);
await import(pathToFileURL(root+'desktop-management-boundary.test.mjs').href);
