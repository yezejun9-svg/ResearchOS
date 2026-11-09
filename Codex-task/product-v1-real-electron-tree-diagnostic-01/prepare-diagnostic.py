"""One-time C-only narrow transformation; never invokes the runner/helper."""
from pathlib import Path
import hashlib
ROOT=Path(__file__).resolve().parent
file=ROOT/"real-electron-flow.mjs"
source=file.read_text(encoding="utf-8")
start=source.index("  const readToken = ")
end=source.index("  const started = ",start)
source=source[:start]+"  // Diagnostic owns an empty fixture directory; no workspace file contents.\n"+source[end:]
source=source.replace("allowed_task_submissions: 1","allowed_task_submissions: 0")
source=source.replace("model_outcome: 'NOT_RUN'","model_outcome: 'NOT_RUN_DIAGNOSTIC_ONLY'")
source=source.replace("NOT_PROVEN_BY_POSITIVE_READ_FIXTURE","NOT_MEASURED_DIAGNOSTIC_ONLY")
source=source.replace("workspace, original_files: originalFiles, prompt_sha256: sha(prompt),","workspace, diagnostic_only: true, workspace_file_contents_read: false,")
start=source.index("      let stdout = '', stderr = '';")
end=source.index("    });\n    const chosen = ",start)
source=source[:start]+"""      const chunks = []; let stdoutBytes = 0, stderr = '';
      helper.stdout.on('data', chunk => {
        stdoutBytes += chunk.length;
        if (stdoutBytes <= 65536) chunks.push(Buffer.from(chunk));
      });
      helper.stderr.on('data', chunk => { if (stderr.length < 16384) stderr += chunk.toString('utf8'); });
      helper.on('error', error => resolve({ exit: null, error: safeText(error.message) }));
      helper.on('close', exit => {
        if (stdoutBytes > 65536) return resolve({ exit, stdout: null, stdout_bytes: stdoutBytes, error: 'DIAGNOSTIC_STDOUT_LIMIT', stderr: safeText(stderr) });
        try {
          const stdout = new TextDecoder('utf-8', { fatal: true }).decode(Buffer.concat(chunks));
          resolve({ exit, stdout, stdout_bytes: stdoutBytes, stderr: safeText(stderr) });
        } catch { resolve({ exit, stdout: null, error: 'DIAGNOSTIC_STDOUT_UTF8', stderr: safeText(stderr) }); }
      });
"""+source[end:]
start=source.index("    write('native-folder-automation.json', chosen);")
end=source.index("\n  } catch (error) {",start)
source=source[:start]+"""    let pickerResult;
    try { pickerResult = parseDiagnosticReply(chosen, core); }
    catch (error) {
      write('native-folder-automation.json', { exit: chosen.exit, error: safeText(error.message),
        stdout_sha256: typeof chosen.stdout === 'string' ? sha(chosen.stdout) : null,
        stdout_bytes: chosen.stdout_bytes, stderr: safeText(chosen.stderr || '') });
      throw error;
    }
    const sanitized = sanitizeDiagnosticScalars(pickerResult);
    write('native-folder-automation.json', { exit: chosen.exit, stdout: JSON.stringify(sanitized),
      stdout_sha256: sha(chosen.stdout), stdout_bytes: chosen.stdout_bytes, stderr: chosen.stderr });
    write('owned-tree-snapshot.json', sanitized.diagnostic);
    state.native_picker_cleanup = sanitized.cleanup;
    state.native_workspace_authorization = sanitized.authorization_state;
    state.native_picker = 'DIAGNOSTIC_OWNED_IDCANCEL_NO_OK';
    state.model_outcome = 'NOT_RUN_DIAGNOSTIC_ONLY';
    state.status = 'OWNED_DIALOG_TREE_DIAGNOSTIC_CAPTURED_NOT_PRODUCT_ACCEPTED';
"""+source[end:]
start=source.index("    state.transport_routes = ")
end=source.index("    write('result.json', state);",start)
source=source[:start]+"""    state.transport_routes = { observation: 'NO_HARNESS_ROUTES_DIAGNOSTIC_ONLY', expected: [] };
    state.outbox_ref_basis = 'NOT_READ_DIAGNOSTIC_ONLY';
"""+source[end:]
source=source.replace("REAL_UI_READONLY_FLOW_OBSERVED_NOT_PRODUCT_ACCEPTED","OWNED_DIALOG_TREE_DIAGNOSTIC_CAPTURED_NOT_PRODUCT_ACCEPTED")
for forbidden in ["window.researchos.harness","submit.click(","readToken","prompt_sha256","getByLabel('Codex","'POST /harness"]:
    if forbidden in source: raise SystemExit("NORMAL_TASK_PATH_REMAINS:"+forbidden)
file.write_text(source,encoding="utf-8")
print("DIAGNOSTIC_RUNNER_WRITTEN_NO_EXECUTION "+hashlib.sha256(file.read_bytes()).hexdigest())
