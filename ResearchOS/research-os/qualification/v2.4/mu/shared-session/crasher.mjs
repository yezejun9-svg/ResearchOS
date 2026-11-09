// Crash-path probe: starts one worker via supervisor, prints its PID, then exits WITHOUT
// cleanup so the OS closes the pipe; harness then checks the worker is not orphaned.
import { SessionSupervisor } from './supervisor.mjs';
import { join } from 'node:path';
const muRoot = process.cwd();
const sup = new SessionSupervisor({ muRoot, workspace: join(muRoot, 'shared-session', '.sandbox'), model: process.env.ROS_QUAL_MODEL || 'deepseek' });
console.log('WORKER_PID=' + sup.child.pid);
// deliberately no exit hooks: emulate host crash by disabling the supervisor's own cleanup
process.removeAllListeners('exit');
process.removeAllListeners('SIGINT');
process.removeAllListeners('SIGTERM');
// stay alive quietly until force-killed by taskkill
setInterval(() => {}, 1000);
