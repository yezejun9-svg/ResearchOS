import test from 'node:test';
import assert from 'node:assert';
import { readFileSync } from 'node:fs';
test('sample contains marker', () => { assert.match(readFileSync('sample.txt','utf8'), /QUALMARK-42/); });
