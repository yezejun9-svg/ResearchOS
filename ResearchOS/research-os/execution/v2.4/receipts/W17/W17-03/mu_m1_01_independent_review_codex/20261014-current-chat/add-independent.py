from pathlib import Path
R=Path(__file__).parent;S=R/'source'
src=(S/'adapters/runtime/mu/worker-pause.test.mjs').read_text()
harness=src.split('\ntest(\n')[0]
assert harness.rstrip().endswith('}')
harness=harness.replace('    withTool = false,','    withTool = false,\n    mutateAck,')
harness=harness.replace('          if (ack === "boolean") {','          mutateAck?.(payload);\n          if (ack === "boolean") {')
extra=r'''
test("independent resume admission rejects tampered identities, ledger, watermarks and cumulative bounds before any effect", { timeout: 45000 }, async t => {
  const first=await run(t);assert.equal(first.code,0,first.stderr);
  assert.equal(first.frames.at(-1).sequence,first.checkpoint.sequence+1);
  const cases={
    foreign_run:s=>s.binding.run_id="other",
    foreign_task:s=>s.binding.task_id="other",
    foreign_project:s=>s.binding.project_id="other",
    foreign_session:s=>s.binding.session_id="other",
    foreign_generation:s=>s.binding.queue_generation="other",
    changed_config:s=>s.config_hash="a".repeat(64),
    over_model_budget:s=>s.counts.model_calls=9,
    fractional_tool_count:s=>s.counts.tool_calls=0.5,
    changed_queue_watermark:s=>s.queue_state.sdk_watermarks.steering++,
    duplicate_command_id:s=>s.commands[1].details.command_id=s.commands[0].details.command_id,
    false_consumed_state:s=>s.commands[0].state="CONSUMED",
    missing_pending_command:s=>s.commands.pop(),
    changed_original_sdk_epoch:s=>s.sdk.payload.binding.leaseEpoch=2,
  };
  for(const [name,mutate] of Object.entries(cases)) await t.test(name,async()=>{
    const altered=JSON.parse(first.raw);mutate(altered);
    const r=await run(t,{snapshot:Buffer.from(JSON.stringify(altered)),epoch:2});
    assert.notEqual(r.code,0,r.stderr);assert.equal(r.effects.length,0);
    assert.ok(!r.frames.some(f=>f.type==="turn.completed"));
  });
  for(const [name,mutateActivation] of Object.entries({missing_carry:a=>delete a.carry_use_receipt_hash,missing_use_principal:a=>delete a.checkpoint_use_principal,non_successor:a=>a.new_epoch=3})) await t.test(name,async()=>{
    const r=await run(t,{snapshot:first.raw,epoch:2,mutateActivation});assert.notEqual(r.code,0);assert.equal(r.effects.length,0);
  });
});
test("independent worker refuses incomplete durable ACK identity",{timeout:30000},async t=>{
  for(const [name,mutateAck] of Object.entries({wrong_sequence:p=>p.checkpoint_sequence++,missing_artifact:p=>delete p.checkpoint_artifact_id,missing_principal:p=>delete p.checkpoint_use_principal,malformed_receipt:p=>p.checkpoint_use_receipt_hash="true",wrong_pause_id:p=>p.pause_id="other"})) await t.test(name,async()=>{
    const r=await run(t,{mutateAck});assert.notEqual(r.code,0);assert.ok(!r.frames.some(f=>f.type==="turn.paused"));
  });
});
'''
(S/'adapters/runtime/mu/independent-review.test.mjs').write_text(harness+extra)
