'use strict';
const deny=n=>()=>{throw Error('QA_REAL_OPERATION_FORBIDDEN:'+n)};
const cp=require('node:child_process');for(const n of ['spawn','spawnSync','exec','execSync','execFile','execFileSync','fork'])cp[n]=deny(n);
const net=require('node:net');net.connect=deny('connect');net.createConnection=deny('createConnection');net.Socket.prototype.connect=deny('Socket.connect');net.Server.prototype.listen=deny('listen');
require('node:tls').connect=deny('tls.connect');globalThis.fetch=deny('fetch');
