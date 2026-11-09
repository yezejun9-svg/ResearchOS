from pathlib import Path
import hashlib
import json

ROOT = Path('D:/作品集/ResearchOS/research-os/.local/worktrees/w14-peer-auth-seam-20261104')
AUTHOR = Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/continue-cp586-20261104/w14-peer-auth-seam/author')
before = json.loads((AUTHOR/'checks01/results.json').read_text(encoding='utf-8'))['sources_after']
for name, digest in before.items():
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == digest, name
path = ROOT/'internal/api/v2_auth_context_test.go'
text = path.read_text(encoding='utf-8')
old = '\tf.v2.svc.Domain = s\n'
assert text.count(old) == 1
text = text.replace(old, old + '\tf.v2.svc.ConfigurationAuthority = commandAuthConfigurationFixture{}\n', 1)
text += '''
// SYNTHETIC configuration metadata completes the ordinary host.status fixture.
// It is neither OS identity evidence nor a native/client attestation.
type commandAuthConfigurationFixture struct{}

func (commandAuthConfigurationFixture) ConfigurationMetadata(_ context.Context, principal, _ string, credential *string) (domain.ClientConfigurationMetadata, error) {
	if principal != "command-owner" || credential != nil {
		return domain.ClientConfigurationMetadata{}, domain.Fail(403, "FORBIDDEN", "synthetic configuration scope")
	}
	return domain.ClientConfigurationMetadata{OwnerHost: "host-123456789abc", Principal: principal}, nil
}
'''
path.write_text(text, encoding='utf-8', newline='\n')
print(json.dumps({'status': 'FIXED_ONLY_NEW_API_FIXTURE_PRECONDITION', 'path': str(path), 'old_sha256': before['internal/api/v2_auth_context_test.go'], 'new_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}))
