'use strict';
// Independent pure QA: no listeners, sockets, CLI/native/model child processes.
const forbidden = name => () => { throw Error('QA_REAL_OPERATION_FORBIDDEN:' + name); };
const net = require('node:net');
net.connect = forbidden('net.connect'); net.createConnection = forbidden('net.createConnection');
net.Server.prototype.listen = forbidden('server.listen');
net.Socket.prototype.connect = forbidden('socket.connect');
const tls = require('node:tls'); tls.connect = forbidden('tls.connect');
const cp = require('node:child_process');
for (const method of ['spawn','spawnSync','exec','execSync','execFile','execFileSync','fork']) cp[method] = forbidden('child.'+method);
globalThis.fetch = forbidden('fetch');
const http = require('node:http'), https = require('node:https');
http.request = forbidden('http.request'); http.get = forbidden('http.get');
https.request = forbidden('https.request'); https.get = forbidden('https.get');
