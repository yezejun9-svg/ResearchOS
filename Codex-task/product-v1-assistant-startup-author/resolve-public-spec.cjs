// The sparse source worktree omits the immutable public OpenAPI file. Supply
// only that exact dependency from Main; no runtime/transport behavior is mocked.
const Module = require('node:module');
const original = Module._resolveFilename;
Module._resolveFilename = function(request, parent, ...rest) {
  if (request === '../../../spec/v2.0/contracts/openapi.json' &&
      parent?.filename.endsWith('tests\\ui\\desktop\\w13-react.test.js')) {
    return 'D:/作品集/ResearchOS/research-os/spec/v2.0/contracts/openapi.json';
  }
  return original.call(this, request, parent, ...rest);
};
