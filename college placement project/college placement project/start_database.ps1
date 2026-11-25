$base = Split-Path -Parent $MyInvocation.MyCommand.Path
$data = Join-Path $base "mysql-data"
$mysqld = "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqld.exe"
if (-not (Test-Path $mysqld)) {
    $found = Get-Command mysqld -ErrorAction SilentlyContinue
    if ($found) { $mysqld = $found.Source }
}
if (-not (Test-Path $mysqld)) { Write-Host "[ERROR] mysqld.exe not found."; exit 1 }
$mysqladmin = Join-Path (Split-Path $mysqld) "mysqladmin.exe"

& $mysqladmin -h 127.0.0.1 -P 3307 -u root --connect-timeout=2 ping *> $null
if ($LASTEXITCODE -eq 0) { Write-Host "[OK] MySQL already running on 127.0.0.1:3307"; exit 0 }

if (-not (Test-Path (Join-Path $data "data"))) {
    Write-Host "Creating database files ..."
    & $mysqld --initialize-insecure --datadir="$data\data" --console *> $null
}

$arg = "--datadir=`"$data\data`" --port=3307 --mysqlx=0 --bind-address=127.0.0.1 --pid-file=`"$data\mysqld.pid`" --log-error=`"$data\error.log`""
Start-Process -FilePath $mysqld -ArgumentList $arg -WindowStyle Hidden

for ($i = 0; $i -lt 40; $i++) {
    & $mysqladmin -h 127.0.0.1 -P 3307 -u root --connect-timeout=2 ping *> $null
    if ($LASTEXITCODE -eq 0) { Write-Host "[OK] MySQL ready on 127.0.0.1:3307"; exit 0 }
    Start-Sleep -Milliseconds 500
}
Write-Host "[ERROR] MySQL did not start. See mysql-data\error.log"
exit 1
