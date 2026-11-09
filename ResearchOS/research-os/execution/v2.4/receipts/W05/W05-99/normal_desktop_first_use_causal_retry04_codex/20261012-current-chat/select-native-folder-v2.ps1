param([Parameter(Mandatory=$true)][int]$ChooserProcessId)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$rootCondition = [System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::ProcessIdProperty, $ChooserProcessId)
$windows = [System.Windows.Automation.AutomationElement]::RootElement.FindAll([System.Windows.Automation.TreeScope]::Children, $rootCondition)
$dialog = $null
foreach ($window in $windows) {
    if ($window.Current.ClassName -eq '#32770' -and -not $window.Current.IsOffscreen) {
        if ($null -ne $dialog) { throw 'Multiple native dialogs for owned Core.' }
        $dialog = $window
    }
}
if ($null -eq $dialog) { throw 'Owned visible native folder dialog missing.' }
$treeItem = [System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::ControlTypeProperty, [System.Windows.Automation.ControlType]::TreeItem)
$computer = $null
for ($attempt = 0; $attempt -lt 20 -and $null -eq $computer; $attempt++) {
    $items = $dialog.FindAll([System.Windows.Automation.TreeScope]::Descendants, $treeItem)
    foreach ($item in $items) {
        if ($item.Current.Name -in @('此电脑', 'This PC', '计算机', 'Computer')) { $computer = $item; break }
    }
    if ($null -eq $computer) { Start-Sleep -Milliseconds 250 }
}
if ($null -eq $computer) { throw 'This PC native tree item missing.' }
([System.Windows.Automation.ExpandCollapsePattern]$computer.GetCurrentPattern([System.Windows.Automation.ExpandCollapsePattern]::Pattern)).Expand()
Start-Sleep -Milliseconds 250
$drive = $null
foreach ($item in $computer.FindAll([System.Windows.Automation.TreeScope]::Children, $treeItem)) {
    if ($item.Current.Name -match '\(D:\)$') { $drive = $item; break }
}
if ($null -eq $drive) { throw 'D drive native tree item missing.' }
$selected = $drive
$steps = @('作品集', 'ResearchOS', 'research-os', '.local', 'worktrees', 'w05-own-cli-product-agent-20261012')
$visited = @($drive.Current.Name)
foreach ($segment in $steps) {
    ([System.Windows.Automation.ExpandCollapsePattern]$selected.GetCurrentPattern([System.Windows.Automation.ExpandCollapsePattern]::Pattern)).Expand()
    Start-Sleep -Milliseconds 150
    $next = $null
    foreach ($item in $selected.FindAll([System.Windows.Automation.TreeScope]::Children, $treeItem)) {
        if ($item.Current.Name -eq $segment) { $next = $item; break }
    }
    if ($null -eq $next) { throw ('Expected native tree child missing: ' + $segment) }
    $selected = $next
    $visited += $segment
}
([System.Windows.Automation.SelectionItemPattern]$selected.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern)).Select()
$selection = [System.Windows.Automation.SelectionItemPattern]$selected.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern)
if (-not $selection.Current.IsSelected) { throw 'Native target tree item not selected.' }
$buttonCondition = [System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::AutomationIdProperty, '1')
$ok = $dialog.FindFirst([System.Windows.Automation.TreeScope]::Descendants, $buttonCondition)
if ($null -eq $ok -or -not $ok.Current.IsEnabled -or $ok.Current.ControlType -ne [System.Windows.Automation.ControlType]::Button) { throw 'Native OK button invalid.' }
$result = [ordered]@{ at = [DateTimeOffset]::UtcNow.ToString('o'); core_pid = $ChooserProcessId; dialog = $dialog.Current.NativeWindowHandle; visible = (-not $dialog.Current.IsOffscreen); selected = $selected.Current.Name; visited = $visited; target = 'D:\作品集\ResearchOS\research-os\.local\worktrees\w05-own-cli-product-agent-20261012'; action = 'WINDOWS_UI_AUTOMATION_SELECTION_AND_NATIVE_INVOKE'; custom_messages = 0; model_calls = 0 }
$result | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'native-uia-selection-v2.intent.json') -Encoding utf8
([System.Windows.Automation.InvokePattern]$ok.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern)).Invoke()
$result | ConvertTo-Json -Depth 5
