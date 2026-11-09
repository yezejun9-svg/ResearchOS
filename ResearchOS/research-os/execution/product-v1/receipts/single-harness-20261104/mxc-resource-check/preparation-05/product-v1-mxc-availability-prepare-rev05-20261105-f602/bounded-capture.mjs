import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

// Fixed-size replacement; .next remains evidence if interrupted before rename.
// Prefix bytes are fsynced before a progress snapshot claims them durable.
export function durableJSON(file, value, io = fs) {
  const next = file + '.next';
  const fd = io.openSync(next, 'wx');
  try { io.writeFileSync(fd, JSON.stringify(value, null, 2) + '\n'); io.fsyncSync(fd); }
  finally { io.closeSync(fd); }
  io.renameSync(next, file);
}
const summary = e => {
  const message=String(e?.message||'');
  return {code:String(e?.code || 'CAPTURE_IO_ERROR').slice(0,80),errno:e?.errno??null,
    message_prefix:message.slice(0,2048),message_sha256:crypto.createHash('sha256').update(message).digest('hex'),message_truncated:message.length>2048};
};
export class BoundedCapture {
  constructor({directory,name,limit=1048576,prefixLimit=65536,onFailure=()=>{},io=fs}) {
    this.io=io; this.directory=directory; this.name=name; this.limit=limit; this.prefixLimit=prefixLimit;
    this.onFailure=onFailure; this.hash=crypto.createHash('sha256'); this.prefixHash=crypto.createHash('sha256');
    this.delivered=0; this.ingested=0; this.prefixBytes=0; this.discardedTail=0; this.sequence=0;
    this.limitReached=false; this.persistenceFailed=false; this.ended=false; this.childClosed=false;
    this.errors=[]; this.stopped=false; this.source=null; this.fd=null;
    this.prefixPath=path.join(directory,name+'.prefix.bin');
    this.progressPath=path.join(directory,name+'.progress.json');
    this.fd=io.openSync(this.prefixPath,'wx');
    io.fsyncSync(this.fd);
    this.persist('OPEN_CHILD_CLOSE_UNCONFIRMED');
    if(this.persistenceFailed) throw Object.assign(new Error('CAPTURE_INITIALIZATION_FAILED'),{code:'CAPTURE_INITIALIZATION_FAILED'});
  }
  attach(source) { this.source=source; }
  pause() { this.stopped=true; this.source?.pause(); }
  state(status='UNKNOWN_CHILD_CLOSE_UNCONFIRMED') {
    const complete=this.childClosed && this.ended && !this.limitReached && !this.persistenceFailed && this.errors.length===0;
    return {schema:'researchos.bounded-native-capture.v1',sequence:this.sequence,status,
      stream:this.name,delivered_bytes:this.delivered,ingested_bytes:this.ingested,discarded_tail_bytes:this.discardedTail,
      durable_prefix_bytes:this.prefixBytes,prefix_sha256:this.prefixHash.copy().digest('hex'),
      ingested_sha256:this.hash.copy().digest('hex'),hash_covers:'INGESTED_BYTES_ONLY',
      stream_complete:complete,complete_stream_sha256:complete?this.hash.copy().digest('hex'):null,
      limit_reached:this.limitReached,persistence_failed:this.persistenceFailed,paused:this.stopped,
      stream_end_observed:this.ended,child_close_observed:this.childClosed,errors:this.errors.slice(),
      resource_ready:false,automatic_retry:false};
  }
  persist(status) {
    this.sequence++;
    try { durableJSON(this.progressPath,this.state(status),this.io); }
    catch(error) {
      this.persistenceFailed=true; this.pause();
      if(this.errors.length<4)this.errors.push(summary(error));
      this.onFailure('CAPTURE_PERSISTENCE_FAILED'); // no exception / no retry / no child kill
    }
  }
  accept(chunk) {
    if(this.stopped)return; // queued data after pause is neither counted nor hashed
    try {
      this.delivered+=chunk.length;
      const accepted=chunk.subarray(0,Math.min(chunk.length,this.limit-this.ingested));
      this.hash.update(accepted); this.ingested+=accepted.length;
      this.discardedTail+=chunk.length-accepted.length;
      const keep=accepted.subarray(0,Math.min(accepted.length,this.prefixLimit-this.prefixBytes));
      if(keep.length) {
        this.io.writeFileSync(this.fd,keep);
        this.io.fsyncSync(this.fd);
        this.prefixHash.update(keep); this.prefixBytes+=keep.length;
      }
      if(this.ingested>=this.limit) { this.limitReached=true; this.pause(); }
      this.persist(this.limitReached?'UNKNOWN_LIMIT_PAUSED_AWAITING_ROOT_JOB':'UNKNOWN_OUTPUT_OBSERVED_CHILD_CLOSE_UNCONFIRMED');
    } catch(error) { this.persistenceFailed=true; this.pause(); this.recordError(error,'UNKNOWN_CAPTURE_WRITE_FAILED'); }
  }
  recordError(error,status='UNKNOWN_STREAM_ERROR') {
    this.pause();
    if(this.errors.length<4)this.errors.push(summary(error));
    this.persist(status);
    this.onFailure(status);
  }
  markTimeout() { this.persist('UNKNOWN_SOFT_TIMEOUT_AWAITING_ROOT_JOB'); }
  markEnd() { this.ended=true; this.persist('EOF_CHILD_CLOSE_UNCONFIRMED'); }
  finish() {
    this.childClosed=true;
    this.persist(this.limitReached||this.errors.length||this.persistenceFailed?'UNKNOWN_CHILD_CLOSED_INCOMPLETE':'CHILD_CLOSED_REQUIRES_ROOT_STOP_PROOF');
    try { if(this.fd!==null) {this.io.closeSync(this.fd);this.fd=null;} }
    catch(error) { this.persistenceFailed=true;this.recordError(error,'UNKNOWN_PREFIX_CLOSE_FAILED'); }
    return this.state('CHILD_CLOSED_REQUIRES_ROOT_STOP_PROOF');
  }
}

