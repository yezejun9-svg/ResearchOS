param([string]$Id,[string]$Body,[string]$Cwd='D:\作品集\ResearchOS\research-os')
$ErrorActionPreference='Stop'
$ev=$PSScriptRoot
$sp=Join-Path $ev "$Id.command.ps1"
[IO.File]::WriteAllText($sp,$Body,[Text.UTF8Encoding]::new($true))
$exe=Join-Path $PSHOME 'pwsh.exe'
$recipe=[ordered]@{id=$Id;fullargv=@($exe,'-NoProfile','-File',$sp);cwd=$Cwd;relevantenv=@{TEMP=$env:TEMP;TMP=$env:TMP;PATH=$env:PATH};rawstdout="$ev\$Id.stdout.txt";rawstderr="$ev\$Id.stderr.txt";nativeexit="$ev\$Id.exit.txt";at=[DateTime]::UtcNow.ToString('o')}
$recipe|ConvertTo-Json -Depth 6|Set-Content "$ev\$Id.recipe.json" -Encoding utf8
$p=Start-Process -FilePath $exe -ArgumentList @('-NoProfile','-File',('"{0}"' -f $sp)) -WorkingDirectory $Cwd -WindowStyle Hidden -RedirectStandardOutput "$ev\$Id.stdout.txt" -RedirectStandardError "$ev\$Id.stderr.txt" -Wait -PassThru
$p.ExitCode|Set-Content "$ev\$Id.exit.txt"
Get-Content "$ev\$Id.stdout.txt" -Raw -Encoding utf8
Get-Content "$ev\$Id.stderr.txt" -Raw -Encoding utf8
exit $p.ExitCode