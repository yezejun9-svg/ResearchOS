const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const Module = require('node:module');
const root = fs.realpathSync(process.env.REVIEW_SOURCE_ROOT);
const output = process.env.REVIEW_BIND_LOG;
const expected = JSON.parse(fs.readFileSync(process.env.REVIEW_BIND_EXPECTED, 'utf8'));
const original = Module._load;
Module._load = function(request, parent, isMain) {
  const resolved = Module._resolveFilename(request, parent, isMain);
  if (typeof resolved === 'string' && /[\\/]apps[\\/]desktop[\\/]main[\\/]lib[\\/]/i.test(resolved)) {
    const actual = fs.realpathSync(resolved);
    const relative = path.relative(root, actual).replaceAll('\\', '/');
    if (relative.startsWith('..') || path.isAbsolute(relative)) throw new Error('REVIEW_SOURCE_ROOT_MISMATCH');
    const hash = crypto.createHash('sha256').update(fs.readFileSync(actual)).digest('hex');
    if (expected[relative] !== hash) throw new Error('REVIEW_FROZEN_SOURCE_HASH_MISMATCH: ' + relative);
    fs.appendFileSync(output + '.' + process.pid + '.jsonl', JSON.stringify({pid:process.pid,request,parent:parent?.filename,resolved:actual,relative,sha256:hash})+'\n');
  }
  return original.apply(this, arguments);
};
