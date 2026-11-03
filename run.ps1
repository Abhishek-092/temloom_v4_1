# TEMLOOM v4.1 — Windows PowerShell Launcher
# Usage:
#   .\run.ps1              # Start with synthetic simulator (default)
#   .\run.ps1 stop         # Kill a running server on port 8080
#   .\run.ps1 test         # Run the 14-suite test runner
#   .\run.ps1 benchmark    # Run the benchmark suite

param(
    [string]$Command = "start"
)

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

switch ($Command) {

    "stop" {
        $procs = Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue |
                 Where-Object State -eq Listen |
                 ForEach-Object { Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue }
        if ($procs) {
            $procs | Stop-Process -Force
            Write-Host "Stopped TEMLOOM server on port 8080."
        } else {
            Write-Host "No server found listening on port 8080."
        }
    }

    "test" {
        Write-Host "Running TEMLOOM v4.1 test suite..."
        python tests/run_all_tests.py
    }

    "benchmark" {
        Write-Host "Running TEMLOOM v4.1 benchmark suite..."
        python benchmarks/run_all_benchmarks.py
    }

    default {
        Write-Host ""
        Write-Host "========================================================"
        Write-Host "  TEMLOOM v4.1 — Air-Gapped Predictive NOC Platform"
        Write-Host "========================================================"
        Write-Host "  Starting FastAPI server on http://127.0.0.1:8080"
        Write-Host "  Press Ctrl+C to stop."
        Write-Host ""
        python -m uvicorn temloom.api_ui.app:app --host 127.0.0.1 --port 8080 --log-level info
    }
}

