<#  Démarre le backend Flask et log tout dans backend_run.log  #>

param(
  [string]$PythonExe = "python",
  [string]$AppPath   = "backend\app.py",
  [string]$LogPath   = "backend\backend_run.log"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSCommandPath
Set-Location $root\..

# Préfixe horodaté dans le log
$ts = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
"==== START backend $ts ====" | Out-File -FilePath $LogPath -Append -Encoding utf8

# Démarre en tâche de fond en redirigeant stdout + stderr
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName  = $PythonExe
$psi.Arguments = $AppPath
$psi.WorkingDirectory = (Resolve-Path ".").Path
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError  = $true
$psi.UseShellExecute = $false
$psi.CreateNoWindow = $true

$proc = New-Object System.Diagnostics.Process
$proc.StartInfo = $psi
$null = $proc.Start()

# Async: pipe stdout/err vers le log
$stdOutEvent = Register-ObjectEvent -InputObject $proc -EventName OutputDataReceived -Action {
  if ($EventArgs.Data) { $EventArgs.Data | Out-File -FilePath $LogPath -Append -Encoding utf8 }
}
$stdErrEvent = Register-ObjectEvent -InputObject $proc -EventName ErrorDataReceived -Action {
  if ($EventArgs.Data) { $EventArgs.Data | Out-File -FilePath $LogPath -Append -Encoding utf8 }
}
$proc.BeginOutputReadLine()
$proc.BeginErrorReadLine()

"Backend lancé (PID=$($proc.Id)). Log: $LogPath"
"Astuce: Stop-Process -Id $($proc.Id) pour l'arrêter."


