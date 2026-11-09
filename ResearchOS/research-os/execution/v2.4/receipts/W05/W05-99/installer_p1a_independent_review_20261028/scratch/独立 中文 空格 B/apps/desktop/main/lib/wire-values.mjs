// Exact values crossing the Desktop private validator/IPC boundary.
const integerPattern = /^-?(0|[1-9][0-9]*)$/;
const numberPattern = /^-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][+-]?[0-9]+)?$/;
const MAX = BigInt(Number.MAX_SAFE_INTEGER);
export function integer(value) {
  return typeof value === 'bigint' || (typeof value === 'number' && Number.isSafeInteger(value));
}
export function asInteger(value) {
  if (!integer(value)) throw new Error('EXACT_INTEGER_REQUIRED');
  return typeof value === 'bigint' ? value : BigInt(value);
}
export function compare(a, b) { const x = asInteger(a), y = asInteger(b); return x < y ? -1 : x > y ? 1 : 0; }
export function previous(value) { const n = asInteger(value); return n > 0n ? n - 1n : 0n; }
export function exactInteger(text) {
  if (typeof text !== 'string' || text.length > 8192 || !integerPattern.test(text)) throw new Error('PRIVATE_NUMERIC_VALUE');
  const n = BigInt(text); return n <= MAX && n >= -MAX ? Number(n) : n;
}
export function stringify(value, pretty = false, byteLimit = 8388608) {
  const seen = new Set(); let nodes = 0, bytes = 0;
  const reserve = n => { bytes += n; if (bytes > byteLimit) throw new Error('LOCAL_RESOURCE_LIMIT'); };
  const quoted = text => {
    let n = 2;
    for (const char of text) {
      const c = char.codePointAt(0);
      if (c >= 0xd800 && c <= 0xdfff) throw new Error('INVALID_LOCAL_UNICODE');
      n += c < 32 ? 6 : c === 34 || c === 92 ? 2 : c < 128 ? 1 : c < 2048 ? 2 : c < 65536 ? 3 : 4;
      if (n > byteLimit) throw new Error('LOCAL_RESOURCE_LIMIT');
    }
    reserve(n); return JSON.stringify(text);
  };
  const encode = (v, depth) => {
    if (++nodes > 262144 || depth > 256) throw new Error('LOCAL_RESOURCE_LIMIT');
    if (v === null) { reserve(4); return 'null'; }
    if (typeof v === 'string') return quoted(v);
    if (typeof v === 'boolean') { reserve(5); return String(v); }
    if (typeof v === 'bigint') {
      const s = String(v); if (s.length > 4097) throw new Error('LOCAL_RESOURCE_LIMIT'); reserve(s.length); return s;
    }
    if (typeof v === 'number') {
      if (!Number.isFinite(v) || !Number.isSafeInteger(v)) throw new Error('AMBIGUOUS_LOCAL_NUMBER');
      const text = String(v); reserve(text.length); return text;
    }
    if (typeof v !== 'object' || seen.has(v)) throw new Error('INVALID_LOCAL_VALUE');
    seen.add(v);
    let result;
    if (Array.isArray(v)) { reserve(v.length + 2); result = '[' + v.map(x => encode(x, depth + 1)).join(',') + ']'; }
    else {
      const proto = Object.getPrototypeOf(v);
      if (proto !== Object.prototype && proto !== null) throw new Error('INVALID_LOCAL_OBJECT');
      const keys = Object.keys(v); reserve(keys.length * 2 + 2);
      result = '{' + keys.map(k => quoted(k) + ':' + encode(v[k], depth + 1)).join(',') + '}';
    }
    seen.delete(v); return result;
  };
  // Exact output deliberately never passes through JSON.parse/JSON.stringify.
  return encode(value, 0);
}
export function display(value) {
  try { return stringify(value, false, 67108864); }
  catch { return '[unavailable exact value]'; }
}
export function reify(tree) {
  let nodes = 0;
  const visit = (node, depth) => {
    if (++nodes > 262144 || depth > 256 || !Array.isArray(node)) throw new Error('PRIVATE_VALUE');
    const [kind, value] = node;
    if (kind === 'null' && node.length === 1) return null;
    if (kind === 'bool' && node.length === 2 && typeof value === 'boolean') return value;
    if (kind === 'string' && node.length === 2 && typeof value === 'string') return value;
    if (kind === 'integer' && node.length === 3 && typeof value === 'string' && numberPattern.test(value)) return exactInteger(node[2]);
    if (kind === 'decimal' && node.length === 4 && typeof value === 'string' && numberPattern.test(value) &&
        integerPattern.test(node[2]) && /^[1-9][0-9]*$/.test(node[3])) {
      // A decimal is display-only data. It is not a renderer-forgeable numeric input tag.
      return Object.freeze({ exact_decimal: value });
    }
    if (kind === 'array' && node.length === 2 && Array.isArray(value)) return value.map(x => visit(x, depth + 1));
    if (kind === 'object' && node.length === 2 && Array.isArray(value)) {
      const result = Object.create(null), names = new Set();
      for (const entry of value) {
        if (!Array.isArray(entry) || entry.length !== 2 || typeof entry[0] !== 'string' || names.has(entry[0])) throw new Error('PRIVATE_VALUE');
        names.add(entry[0]); Object.defineProperty(result, entry[0], { value: visit(entry[1], depth + 1), enumerable: true, writable: true, configurable: true });
      }
      return result;
    }
    throw new Error('PRIVATE_VALUE');
  };
  return visit(tree, 0);
}
