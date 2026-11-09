param([int]$DesktopPid,[string]$OutputPath)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$condition=[System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::ProcessIdProperty,$DesktopPid)
$deadline=[DateTime]::UtcNow.AddSeconds(25)
do {
  $windows=[System.Windows.Automation.AutomationElement]::RootElement.FindAll([System.Windows.Automation.TreeScope]::Children,$condition)
  $rows=@()
  foreach($window in $windows) {
    $children=$window.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
    $rows+=@([pscustomobject]@{hwnd=$window.Current.NativeWindowHandle;title=$window.Current.Name;children=@($children|ForEach-Object{[pscustomobject]@{name=$_.Current.Name;id=$_.Current.AutomationId;type=$_.Current.ControlType.ProgrammaticName;hwnd=$_.Current.NativeWindowHandle}})})
  }
  $detail=@($rows.children | Where-Object {$_.name.StartsWith('主机：')})
  if($detail.Count -eq 1) {break}
  Start-Sleep -Milliseconds 200
} while([DateTime]::UtcNow -lt $deadline)
if($detail.Count -ne 1) {throw 'Expected privileged coding dialog absent'}
$bytes=[Text.UTF8Encoding]::new($false).GetBytes(($rows|ConvertTo-Json -Depth 7))
$stream=[IO.File]::Open($OutputPath,[IO.FileMode]::CreateNew)
try {$stream.Write($bytes,0,$bytes.Length)} finally {$stream.Dispose()}
Write-Output 'Observed native coding detail captured; no button clicked by capture.'
