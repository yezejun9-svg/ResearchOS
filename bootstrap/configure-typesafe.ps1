param([switch]$Check, [switch]$SelfTest, [switch]$UiSelfTest)
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSHOME 'Modules\Microsoft.PowerShell.Security\Microsoft.PowerShell.Security.psd1') -ErrorAction Stop
$secretRoot = Join-Path (Split-Path $PSScriptRoot -Parent) '.local\secrets'
$secretPath = Join-Path $secretRoot 'typesafe.dpapi'
if ($UiSelfTest) {
    $secretRoot = Join-Path (Split-Path $secretRoot -Parent) ('credential-ui-test-' + [guid]::NewGuid().ToString())
    $secretPath = Join-Path $secretRoot 'sample.dpapi'
}

function Save-EncryptedCredential([Security.SecureString]$Value, [string]$Destination) {
    $directory = Split-Path $Destination -Parent
    New-Item -ItemType Directory -Path $directory -Force | Out-Null
    $sid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User
    $acl = Get-Acl -LiteralPath $directory
    $acl.SetAccessRuleProtection($true, $false)
    foreach ($oldRule in @($acl.Access)) { [void]$acl.RemoveAccessRuleSpecific($oldRule) }
    $rule = New-Object System.Security.AccessControl.FileSystemAccessRule($sid, 'FullControl', 'ContainerInherit,ObjectInherit', 'None', 'Allow')
    $acl.AddAccessRule($rule)
    # Windows PowerShell Set-Acl also attempts to write the SACL and requires SeSecurityPrivilege.
    # The .NET Framework call persists only the modified access rules.
    if ($PSVersionTable.PSVersion.Major -lt 6) { [IO.Directory]::SetAccessControl($directory, $acl) }
    else { [IO.FileSystemAclExtensions]::SetAccessControl([IO.DirectoryInfo]::new($directory), $acl) }
    $tempPath = Join-Path $directory ([guid]::NewGuid().ToString() + '.tmp')
    try {
        [IO.File]::WriteAllText($tempPath, (ConvertFrom-SecureString -SecureString $Value))
        $roundtrip = Get-Content -LiteralPath $tempPath -Raw | ConvertTo-SecureString
        try { if ($roundtrip.Length -ne $Value.Length) { throw 'Encrypted credential check failed' } }
        finally { $roundtrip.Dispose() }
        Move-Item -LiteralPath $tempPath -Destination $Destination -Force
    } finally {
        if (Test-Path -LiteralPath $tempPath) { Remove-Item -LiteralPath $tempPath }
    }
}

if ($SelfTest) {
    $sample = ConvertTo-SecureString 'ResearchOS-self-check-only' -AsPlainText -Force
    $cipher = ConvertFrom-SecureString $sample
    $restored = ConvertTo-SecureString $cipher
    if ($restored.Length -ne $sample.Length -or $cipher.Contains('ResearchOS-self-check-only')) { throw 'DPAPI roundtrip failed' }
    $restored.Dispose()
    $rejected = $false
    try { $invalid = ConvertTo-SecureString ($cipher.Substring(0, $cipher.Length - 8)) } catch { $rejected = $true }
    if (-not $rejected) { $invalid.Dispose(); throw 'Corrupt credential was not rejected' }
    $testRoot = Join-Path (Split-Path $secretRoot -Parent) ('credential-selftest-' + [guid]::NewGuid().ToString())
    $testPath = Join-Path $testRoot 'sample.dpapi'
    try {
        Save-EncryptedCredential $sample $testPath
        Save-EncryptedCredential $sample $testPath
        $saved = Get-Content -LiteralPath $testPath -Raw | ConvertTo-SecureString
        try { if ($saved.Length -ne $sample.Length) { throw 'Saved credential check failed' } }
        finally { $saved.Dispose() }
        $savedAcl = Get-Acl -LiteralPath $testRoot
        $sid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value
        if (-not $savedAcl.AreAccessRulesProtected -or @($savedAcl.Access).Count -ne 1 -or
            $savedAcl.Access[0].IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value -ne $sid) {
            throw 'Credential directory access check failed'
        }
    } finally {
        $sample.Dispose()
        if (Test-Path -LiteralPath $testPath) { Remove-Item -LiteralPath $testPath }
        if (Test-Path -LiteralPath $testRoot) { Remove-Item -LiteralPath $testRoot }
    }
    @{ status = 'PASS'; assertions = @('DPAPI_CURRENT_USER_ROUNDTRIP', 'CORRUPT_CIPHERTEXT_REJECTED', 'SAVE_AND_REPLACE', 'CURRENT_USER_ONLY_ACL'); live_verified = $false } | ConvertTo-Json
    exit 0
}

if ($Check) {
    $present = Test-Path -LiteralPath $secretPath
    $decryptable = $false
    if ($present) {
        $secured = Get-Content -LiteralPath $secretPath -Raw | ConvertTo-SecureString
        $decryptable = $secured.Length -gt 0
        $secured.Dispose()
    }
    @{ credential = 'TYPESAFE_API_KEY'; configured = $present; decryptable_for_current_user = $decryptable; live_verified = $false } | ConvertTo-Json
    exit $(if ($decryptable) { 0 } else { 2 })
}

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$form = New-Object System.Windows.Forms.Form
$form.Text = 'ResearchOS - TypeSafe API key (v3)'
$form.ClientSize = New-Object System.Drawing.Size(520, 190)
$form.StartPosition = 'CenterScreen'
$form.FormBorderStyle = 'FixedDialog'
$form.MaximizeBox = $false
$form.MinimizeBox = $false

$label = New-Object System.Windows.Forms.Label
$label.Text = 'Enter your TypeSafe API key. Saved locally with Windows DPAPI encryption.'
$label.Location = New-Object System.Drawing.Point(20, 18)
$label.Size = New-Object System.Drawing.Size(480, 40)
$form.Controls.Add($label)

$inputBox = New-Object System.Windows.Forms.TextBox
$inputBox.UseSystemPasswordChar = $true
$inputBox.Location = New-Object System.Drawing.Point(20, 65)
$inputBox.Size = New-Object System.Drawing.Size(480, 28)
$inputBox.AccessibleName = 'TypeSafe API key'
$form.Controls.Add($inputBox)

$status = New-Object System.Windows.Forms.Label
$status.Text = 'This window does not send API requests or print the key.'
$status.Location = New-Object System.Drawing.Point(20, 102)
$status.Size = New-Object System.Drawing.Size(480, 30)
$form.Controls.Add($status)

$save = New-Object System.Windows.Forms.Button
$save.Text = 'Save encrypted'
$save.Location = New-Object System.Drawing.Point(355, 145)
$save.Size = New-Object System.Drawing.Size(145, 30)
$form.Controls.Add($save)
$form.AcceptButton = $save
$save.Add_Click({
    if ([string]::IsNullOrWhiteSpace($inputBox.Text)) {
        $status.Text = 'Enter a non-empty API key.'
        return
    }
    try {
        $secure = ConvertTo-SecureString -String $inputBox.Text.Trim() -AsPlainText -Force
        try {
            Save-EncryptedCredential $secure $secretPath
        } finally {
            $secure.Dispose()
        }
        $inputBox.Clear()
        $form.DialogResult = [System.Windows.Forms.DialogResult]::OK
        $form.Close()
    } catch {
        $status.Text = 'Save failed (' + $_.Exception.GetType().Name + '). The key remains here; no key was logged.'
        if ($UiSelfTest) {
            @{ status = 'FAIL'; error_type = $_.Exception.GetType().Name; command = $_.InvocationInfo.MyCommand.Name; scope = 'SYNTHETIC_UI_ONLY' } | ConvertTo-Json
            $form.Close()
        }
    }
})
if ($UiSelfTest) {
    $inputBox.Text = 'ResearchOS-ui-self-check-only'
    $form.Add_Shown({ $save.PerformClick() })
}
[void]$form.ShowDialog()
$inputBox.Clear()
$form.Dispose()
if ($UiSelfTest) {
    $passed = Test-Path -LiteralPath $secretPath
    if ($passed) {
        $saved = Get-Content -LiteralPath $secretPath -Raw | ConvertTo-SecureString
        try { $passed = $saved.Length -eq 'ResearchOS-ui-self-check-only'.Length }
        finally { $saved.Dispose() }
        Remove-Item -LiteralPath $secretPath
    }
    if (Test-Path -LiteralPath $secretRoot) { Remove-Item -LiteralPath $secretRoot }
    @{ status = $(if ($passed) { 'PASS' } else { 'FAIL' }); assertions = @('WINFORMS_SAVE_BUTTON_DPAPI_ROUNDTRIP'); scope = 'SYNTHETIC_UI_ONLY'; live_verified = $false } | ConvertTo-Json
    exit $(if ($passed) { 0 } else { 1 })
}
