import assert from 'node:assert/strict';
import { webcrypto } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { stripTypeScriptTypes } from 'node:module';
import test from 'node:test';
import { createContext, SourceTextModule, SyntheticModule } from 'node:vm';

// Evaluate the production module with isolated environment variables and mocked
// imports. No vendor installation, real callback listener or network is used.
const sourceUrl = new URL('../../third_party/mu/packages/kyrn-judge/src/google-login/oauth.ts', import.meta.url);
const source = stripTypeScriptTypes(readFileSync(sourceUrl, 'utf8'), { mode: 'strip' });
const providers = [
  { config: 'GEMINI_CLI_LOGIN', auth: 'geminiCliOAuth', prefix: 'MU_GEMINI_CLI' },
  { config: 'ANTIGRAVITY_LOGIN', auth: 'antigravityOAuth', prefix: 'MU_ANTIGRAVITY' },
];

async function load(env = {}) {
  const calls = { prompt: 0, notify: 0, server: 0, fetch: [] };
  const context = createContext({
    process: { env: { ...env } },
    URL, URLSearchParams, AbortController, TextEncoder, Uint8Array,
    crypto: webcrypto, btoa,
    fetch: async (url, options) => {
      calls.fetch.push({ url, options });
      return { ok: true, status: 200, text: async () => JSON.stringify({
        access_token: 'fixture-access', refresh_token: 'fixture-new-refresh', expires_in: 3600,
      }) };
    },
  });
  const imports = {
    'node:http': { createServer: () => { calls.server++; throw new Error('Unexpected callback listener'); } },
    '@earendil-works/pi-ai': { oauthErrorHtml: () => '', oauthSuccessHtml: () => '' },
    './endpoints.ts': { ANTIGRAVITY_ENDPOINTS: ['https://fixture.invalid/antigravity'], CLOUD_CODE_ENDPOINT: 'https://fixture.invalid/code' },
  };
  // Expose the private token boundary only inside this test VM.
  const module = new SourceTextModule(`${source}\nexport { tokenRequest as testTokenRequest };\n`, {
    context, identifier: sourceUrl.href,
  });
  await module.link(specifier => {
    const exports = imports[specifier];
    assert.ok(exports, `Unexpected dependency: ${specifier}`);
    return new SyntheticModule(Object.keys(exports), function () {
      for (const [name, value] of Object.entries(exports)) this.setExport(name, value);
    }, { context });
  });
  await module.evaluate();
  const interaction = {
    signal: new AbortController().signal,
    prompt: async () => { calls.prompt++; return 'cancel'; },
    notify: () => { calls.notify++; },
  };
  return { exports: module.namespace, calls, interaction };
}

function assertNoEffects(calls) {
  assert.equal(calls.prompt, 0);
  assert.equal(calls.notify, 0);
  assert.equal(calls.server, 0);
  assert.equal(calls.fetch.length, 0);
}

const credential = { type: 'oauth', access: 'fixture-old-access', refresh: 'fixture-refresh', expires: 0, projectId: 'fixture-project' };

test('import succeeds without OAuth configuration and performs no interactions or requests', async () => {
  const loaded = await load();
  for (const provider of providers) {
    assert.equal(loaded.exports[provider.config].clientId, '');
    assert.equal(loaded.exports[provider.config].clientSecret, '');
    assert.equal(typeof loaded.exports[provider.auth].login, 'function');
  }
  assertNoEffects(loaded.calls);
});

for (const provider of providers) {
  const idKey = `${provider.prefix}_CLIENT_ID`;
  const secretKey = `${provider.prefix}_CLIENT_SECRET`;
  const cases = [
    { name: 'both missing', env: {}, missing: [idKey, secretKey] },
    { name: 'ID missing', env: { [secretKey]: 'fixture-secret' }, missing: [idKey] },
    { name: 'secret missing', env: { [idKey]: 'fixture-client' }, missing: [secretKey] },
    { name: 'blank configuration', env: { [idKey]: ' \t', [secretKey]: '\r\n' }, missing: [idKey, secretKey] },
  ];
  for (const sample of cases) {
    test(`${provider.prefix}: ${sample.name} fails before login, refresh and token-request effects`, async () => {
      const loaded = await load(sample.env);
      const expected = error => {
        assert.match(error.message, /OAuth client is not configured/);
        for (const key of sample.missing) assert.ok(error.message.includes(key));
        assert.doesNotMatch(error.message, /fixture-secret|fixture-client/);
        return true;
      };
      await assert.rejects(loaded.exports[provider.auth].login(loaded.interaction), expected);
      await assert.rejects(loaded.exports[provider.auth].refresh(credential, loaded.interaction.signal), expected);
      await assert.rejects(loaded.exports.testTokenRequest(loaded.exports[provider.config], {
        grant_type: 'refresh_token', refresh_token: credential.refresh,
      }, loaded.interaction.signal), expected);
      assertNoEffects(loaded.calls);
    });
  }

  test(`${provider.prefix}: configured login reaches consent without opening a listener on cancellation`, async () => {
    const loaded = await load({ [idKey]: 'fixture-client', [secretKey]: 'fixture-secret' });
    await assert.rejects(loaded.exports[provider.auth].login(loaded.interaction), /Login cancelled/);
    assert.equal(loaded.calls.prompt, 1);
    assert.equal(loaded.calls.notify, 0);
    assert.equal(loaded.calls.server, 0);
    assert.equal(loaded.calls.fetch.length, 0);
  });
}

test('each provider injects only its configured client into the token request', async () => {
  const configured = Object.fromEntries(providers.flatMap(provider => [
    [`${provider.prefix}_CLIENT_ID`, `fixture-${provider.prefix}-client`],
    [`${provider.prefix}_CLIENT_SECRET`, `fixture-${provider.prefix}-secret`],
  ]));
  const loaded = await load(configured);
  for (const provider of providers) {
    const config = loaded.exports[provider.config];
    assert.equal(config.clientId, configured[`${provider.prefix}_CLIENT_ID`]);
    assert.equal(config.clientSecret, configured[`${provider.prefix}_CLIENT_SECRET`]);
    const updated = await loaded.exports[provider.auth].refresh(credential, loaded.interaction.signal);
    const request = loaded.calls.fetch.at(-1);
    assert.equal(request.url, config.tokenUrl);
    assert.equal(request.options.body.get('client_id'), config.clientId);
    assert.equal(request.options.body.get('client_secret'), config.clientSecret);
    assert.equal(request.options.body.get('grant_type'), 'refresh_token');
    assert.equal(request.options.body.get('refresh_token'), credential.refresh);
    assert.equal(updated.access, 'fixture-access');
    assert.equal(updated.refresh, 'fixture-new-refresh');
    assert.equal(updated.projectId, credential.projectId);
  }
  assert.equal(loaded.calls.fetch.length, providers.length);
  assert.equal(loaded.calls.prompt, 0);
  assert.equal(loaded.calls.notify, 0);
  assert.equal(loaded.calls.server, 0);
});
