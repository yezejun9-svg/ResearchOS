$ErrorActionPreference = 'Stop'
$repo = 'D:/作品集/ResearchOS/research-os/.local/worktrees/w05-normal-runtime-host-20261012'
$binary = 'D:/作品集/ResearchOS/research-os/.local/builds/normal-runtime-host-candidate-20261012/researchos-control.exe'
$receipts = Split-Path -Parent $PSCommandPath
$assets = 'D:/作品集/ResearchOS/research-os/.local/builds/current-chat-runtime-assets-20261012'
$env:RESEARCHOS_WEB_DIR = 'D:/作品集/ResearchOS/research-os/apps/web/dist'
$results = @()
foreach ($leg in @('production-assets')) {
    $dataRoot = 'D:/作品集/ResearchOS/research-os/.local/normal-runtime-host-smoke-' + $leg + '-' + [guid]::NewGuid().ToString('N')
    New-Item -ItemType Directory -Path $dataRoot | Out-Null
    $env:RESEARCHOS_DATA_DIR = $dataRoot
    $env:RESEARCHOS_LISTEN = '127.0.0.1:0'
    $discovery = Join-Path $dataRoot 'discovery.json'
    $arguments = @('--discovery-file', $discovery)
    if ($leg -eq 'production-assets') { $arguments += @('--runtime-assets-dir', $assets) }
    $process = Start-Process -FilePath $binary -ArgumentList $arguments -WorkingDirectory $repo -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $receipts ('attempt14-' + $leg + '-stdout.txt')) -RedirectStandardError (Join-Path $receipts ('attempt14-' + $leg + '-stderr.txt'))
    try {
        $deadline = [DateTime]::UtcNow.AddSeconds(15)
        while (!(Test-Path -LiteralPath $discovery) -and !$process.HasExited -and [DateTime]::UtcNow -lt $deadline) { Start-Sleep -Milliseconds 100 }
        if ($process.HasExited -or !(Test-Path -LiteralPath $discovery)) { throw 'control startup failed' }
        $hostInfo = Get-Content -LiteralPath $discovery -Raw | ConvertFrom-Json
        $pipe = [IO.Pipes.NamedPipeClientStream]::new('.', ('ResearchOSHost-v1-' + $hostInfo.host_instance_id.Substring(5)), [IO.Pipes.PipeDirection]::InOut)
        try {
            $pipe.Connect(5000)
            $request = @{kind='NATIVE_USER_BOOTSTRAP_REQUEST';client_id='offline-smoke';payload=@{}} | ConvertTo-Json -Compress
            $raw = [Text.Encoding]::UTF8.GetBytes($request)
            $pipe.Write($raw, 0, $raw.Length)
            $buffer = [byte[]]::new(8192)
            $length = $pipe.Read($buffer, 0, $buffer.Length)
            $bootstrap = [Text.Encoding]::UTF8.GetString($buffer, 0, $length) | ConvertFrom-Json
            if ($bootstrap.kind -ne 'NATIVE_USER_BOOTSTRAP_RESULT') { throw 'native bootstrap failed' }
        } finally { $pipe.Dispose() }
        $session = Get-Content -LiteralPath (Join-Path $dataRoot 'host/session.json') -Raw | ConvertFrom-Json
        $headers = @{Authorization=('Bearer ' + $session.token)}
        $envelope = @{protocol_version='researchos-client/2';command_id=[guid]::NewGuid().ToString('N');client_id='offline-smoke';project_id=$null;session_id=$null;expected_revision=$null;writer_epoch=$null;method='host.configure';payload=@{config_revision=1;provider_id='ollama';base_url='http://127.0.0.1:1/v1';model_id='qwen3:4b-instruct';credential_ref=$null}}
        $configured = Invoke-RestMethod -Method Post -Uri ($hostInfo.url + '/v2/command') -Headers $headers -ContentType 'application/json' -Body ($envelope | ConvertTo-Json -Depth 5 -Compress) -TimeoutSec 10
        if ($configured.status -ne 'COMPLETED') { throw 'ordinary host.configure failed' }
        # Drive only the real Shell chooser owned by this exact fresh control process.
        Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
using System.Text;
public static class LocalSetupChooser {
 public delegate bool Callback(IntPtr window, IntPtr data);
 [DllImport("user32.dll")] public static extern bool EnumWindows(Callback callback, IntPtr data);
 [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr window, out uint process);
 [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetClassName(IntPtr window, StringBuilder name, int size);
 [DllImport("user32.dll")] public static extern IntPtr GetDlgItem(IntPtr dialog, int id);
 [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr window, uint message, IntPtr w, IntPtr l);
 public static IntPtr Find(uint process) { IntPtr found=IntPtr.Zero; EnumWindows((w,d)=>{uint p; GetWindowThreadProcessId(w,out p); var s=new StringBuilder(256); GetClassName(w,s,256); if(p==process && s.ToString()=="#32770") {found=w; return false;} return true;},IntPtr.Zero); return found; }
}
"@
        $workspacePath = Join-Path $dataRoot 'selected-empty-workspace'
        New-Item -ItemType Directory -Path $workspacePath | Out-Null
        $chooserPipe = [IO.Pipes.NamedPipeClientStream]::new('.', ('ResearchOSHost-v1-' + $hostInfo.host_instance_id.Substring(5)), [IO.Pipes.PipeDirection]::InOut)
        try {
            $chooserPipe.Connect(5000)
            $chooseFrame=@{kind='NATIVE_WORKSPACE_CHOOSE_REQUEST';client_id='offline-smoke';payload=@{requested_path=$workspacePath;requested_access='READ_ONLY'}} | ConvertTo-Json -Compress
            $chooseBytes=[Text.Encoding]::UTF8.GetBytes($chooseFrame)
            $chooserPipe.Write($chooseBytes,0,$chooseBytes.Length)
            $dialog=[IntPtr]::Zero
            $chooserDeadline=[DateTime]::UtcNow.AddSeconds(10)
            while($dialog -eq [IntPtr]::Zero -and [DateTime]::UtcNow -lt $chooserDeadline) { $dialog=[LocalSetupChooser]::Find([uint32]$process.Id); Start-Sleep -Milliseconds 100 }
            if($dialog -eq [IntPtr]::Zero) { throw 'real process Shell chooser missing' }
            Start-Sleep -Milliseconds 200
            $okButton=[LocalSetupChooser]::GetDlgItem($dialog,1)
            if($okButton -eq [IntPtr]::Zero) { throw 'real chooser OK button missing' }
            [LocalSetupChooser]::PostMessage($okButton,0x00F5,[IntPtr]::Zero,[IntPtr]::Zero) | Out-Null
            $chooseBuffer=[byte[]]::new(8192)
            $read=$chooserPipe.ReadAsync($chooseBuffer,0,$chooseBuffer.Length)
            if(!$read.Wait(10000)) { throw 'real chooser reply timed out' }
            $chosen=[Text.Encoding]::UTF8.GetString($chooseBuffer,0,$read.Result) | ConvertFrom-Json
            if($chosen.kind -ne 'NATIVE_WORKSPACE_CHOOSE_RESULT' -or $chosen.payload.display_path.Replace('\','/') -ne $workspacePath.Replace('\','/')) { throw 'real chooser returned another directory' }
        } finally { $chooserPipe.Dispose() }
        $envelope.command_id=[guid]::NewGuid().ToString('N'); $envelope.method='workspace.register'; $envelope.payload=@{selection_ref=$chosen.payload.selection_ref;display_name='cold-start smoke workspace';requested_access='READ_ONLY'}
        $registered=Invoke-RestMethod -Method Post -Uri ($hostInfo.url+'/v2/command') -Headers $headers -ContentType 'application/json' -Body ($envelope | ConvertTo-Json -Depth 5 -Compress) -TimeoutSec 10
        if($registered.status -ne 'COMPLETED') { throw ('normal workspace.register failed: '+($registered | ConvertTo-Json -Depth 8 -Compress)) }
        $envelope.command_id=[guid]::NewGuid().ToString('N'); $envelope.method='project.bootstrap'; $envelope.payload=@{authorized_workspace_ref=$registered.result.authorized_workspace_ref;display_name='cold-start smoke project'}
        $project=Invoke-RestMethod -Method Post -Uri ($hostInfo.url+'/v2/command') -Headers $headers -ContentType 'application/json' -Body ($envelope | ConvertTo-Json -Depth 5 -Compress) -TimeoutSec 10
        if($project.status -ne 'COMPLETED') { throw ('normal project.bootstrap failed: '+($project | ConvertTo-Json -Depth 8 -Compress)) }
        $envelope.command_id=[guid]::NewGuid().ToString('N'); $envelope.method='session.create'; $envelope.project_id=$project.result.project_id; $envelope.payload=@{workspace_ref=$registered.result.authorized_workspace_ref;model_config_ref=$configured.result.model_config_ref;title='cold-start smoke session'}
        $created=Invoke-RestMethod -Method Post -Uri ($hostInfo.url+'/v2/command') -Headers $headers -ContentType 'application/json' -Body ($envelope | ConvertTo-Json -Depth 5 -Compress) -TimeoutSec 10
        if($created.status -ne 'COMPLETED') { throw ('normal session.create failed: '+($created | ConvertTo-Json -Depth 8 -Compress)) }
        Start-Sleep -Seconds 2
        $envelope.project_id=$null
        $envelope.command_id = [guid]::NewGuid().ToString('N'); $envelope.method = 'host.status'; $envelope.payload = @{}
        $status = Invoke-RestMethod -Method Post -Uri ($hostInfo.url + '/v2/command') -Headers $headers -ContentType 'application/json' -Body ($envelope | ConvertTo-Json -Depth 5 -Compress) -TimeoutSec 10
        if ($status.status -ne 'COMPLETED' -or $status.result.config_revision -ne 1) { throw 'host.status did not preserve configuration' }
        $results += @{leg=$leg;data_root=$dataRoot;binary_sha256=(Get-FileHash -LiteralPath $binary -Algorithm SHA256).Hash.ToLowerInvariant();native_os_bootstrap='PASSED';ordinary_configure='COMPLETED';config_revision=$status.result.config_revision;configured_models=@($status.result.model_configurations).Count;no_project_created=$false;workspace_selection='REAL_SHELL_CHOOSER';workspace_register=$registered.status;project_bootstrap=$project.status;session_create=$created.status;session_id=$created.session_id;project_id=$project.result.project_id;model_endpoint='unreachable-loopback-fixture';qualification='NOT_RUN'}
    } finally {
        if (!$process.HasExited) { $process.Kill(); $process.WaitForExit(10000) | Out-Null }
        $process.Dispose()
        $session = $null; $headers = $null
    }
}
$results | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $receipts 'control-cold-session-smoke.json') -Encoding utf8NoBOM
$results | Select-Object leg,native_os_bootstrap,ordinary_configure,config_revision,configured_models,qualification | ConvertTo-Json -Depth 3



