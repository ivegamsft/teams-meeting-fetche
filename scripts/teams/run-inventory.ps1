#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Run Teams Configuration Inventory with pre-flight checks (Windows PowerShell)

.DESCRIPTION
    Audits and documents Teams bot configuration. Requires Azure CLI and Python.

.PARAMETER CheckOnly
    Only check prerequisites, don't run inventory

.PARAMETER SkipChecks
    Skip prerequisite checks and run inventory directly

.PARAMETER ArchiveOnly
    Only create archive of existing inventory

.EXAMPLE
    .\scripts\teams\run-inventory.ps1
    .\scripts\teams\run-inventory.ps1 -CheckOnly
    .\scripts\teams\run-inventory.ps1 -ArchiveOnly

.NOTES
    Requires: Azure CLI, Python 3.8+, .env.local file
#>

[CmdletBinding()]
param(
    [switch]$CheckOnly,
    [switch]$SkipChecks,
    [switch]$ArchiveOnly
)

$ErrorActionPreference = "Continue"

# Resolve repo root so relative paths work from any current directory
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$EnvFilePath = Join-Path $RepoRoot ".env.local"
$InventoryPath = Join-Path $RepoRoot "inventory"
$InventoryScriptPath = Join-Path $RepoRoot "scripts\teams\inventory-teams-config.py"

# Colors for output
$Colors = @{
    Success = "Green"
    Warning = "Yellow"
    Error   = "Red"
    Info    = "Cyan"
}

function Write-Header {
    param([string]$Message)
    Write-Host ""
    Write-Host ("=" * 80) -ForegroundColor $Colors.Info
    Write-Host $Message -ForegroundColor $Colors.Info
    Write-Host ("=" * 80) -ForegroundColor $Colors.Info
}

function Write-Check {
    param(
        [string]$Message,
        [bool]$Passed
    )
    $status = if ($Passed) { 
        Write-Host "  ✓" -ForegroundColor $Colors.Success -NoNewline
    } else {
        Write-Host "  ✗" -ForegroundColor $Colors.Error -NoNewline
    }
    Write-Host " $Message"
}

function Test-Prerequisites {
    Write-Header "Checking Prerequisites"
    
    $allPass = $true
    
    # Check Python
    try {
        $pythonVersion = & python --version 2>&1
        $versionMatch = $pythonVersion -match '(\d+)\.(\d+)\.(\d+)'
        if ($versionMatch) {
            $major = [int]$matches[1]
            $minor = [int]$matches[2]
            if ($major -gt 3 -or ($major -eq 3 -and $minor -ge 8)) {
                Write-Check "Python 3.8+" $true
            } else {
                Write-Check "Python 3.8+ (found: $pythonVersion)" $false
                $allPass = $false
            }
        } else {
            Write-Check "Python 3.8+ (found: $pythonVersion)" $false
            $allPass = $false
        }
    } catch {
        Write-Check "Python installed" $false
        Write-Host "    Install from: https://www.python.org/" -ForegroundColor $Colors.Warning
        $allPass = $false
    }
    
    # Check Azure CLI
    try {
        $null = & az --version 2>&1
        Write-Check "Azure CLI installed" $true
    } catch {
        Write-Check "Azure CLI installed" $false
        Write-Host "    Install from: https://aka.ms/azurecli" -ForegroundColor $Colors.Warning
        $allPass = $false
    }
    
    # Check .env.local
    $envFile = Get-Item $EnvFilePath -ErrorAction SilentlyContinue
    Write-Check ".env.local exists" ($null -ne $envFile)
    
    # Check inventory directory
    $invDir = Get-Item $InventoryPath -ErrorAction SilentlyContinue
    Write-Check "inventory/ directory" ($null -ne $invDir)
    
    # Check Python script
    $scriptPath = Get-Item $InventoryScriptPath -ErrorAction SilentlyContinue
    Write-Check "inventory script exists" ($null -ne $scriptPath)
    
    return $allPass
}

function Test-EnvironmentVariables {
    Write-Host ""
    Write-Host "Checking environment variables in .env.local..." -ForegroundColor $Colors.Info
    
    # Load .env.local
    if ((Test-Path $EnvFilePath) -eq $false) {
        Write-Host "  ✗ .env.local not found" -ForegroundColor $Colors.Error
        return $false
    }
    
    $envContent = Get-Content $EnvFilePath -Raw
    $vars = @{}
    
    foreach ($line in $envContent -split "`n") {
        if ($line -match '^\s*([^#=]+)=(.+)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim().Trim('"')
            $vars[$key] = $value
        }
    }
    
    $requiredVars = @(
        "GRAPH_TENANT_ID",
        "GRAPH_CLIENT_ID",
        "ENTRA_GROUP_ID",
        "AWS_WEBHOOK_ENDPOINT"
    )
    
    $allSet = $true
    foreach ($var in $requiredVars) {
        $value = $vars[$var] ?? "NOT SET"
        
        if ($value -eq "NOT SET" -or $value.StartsWith("<")) {
            Write-Check "$var" $false
            Write-Host "    Value: NOT SET or placeholder" -ForegroundColor $Colors.Warning
            $allSet = $false
        } else {
            $display = if ($value.Length -gt 10) { 
                $value.Substring(0, 10) + "..." 
            } else { 
                $value 
            }
            Write-Check "$var" $true
            Write-Host "    Value: $display" -ForegroundColor $Colors.Info
        }
    }
    
    return $allSet
}

function Start-InventoryAudit {
    Write-Header "Running Teams Configuration Inventory"
    
    try {
        $pythonExe = (Get-Command python).Path
        & $pythonExe $InventoryScriptPath
        
        if ($LASTEXITCODE -eq 0) {
            return $true
        } else {
            Write-Host "Inventory failed with exit code: $LASTEXITCODE" -ForegroundColor $Colors.Error
            return $false
        }
    } catch {
        Write-Host "Error running inventory: $_" -ForegroundColor $Colors.Error
        return $false
    }
}

function New-InventoryArchive {
    Write-Host ""
    Write-Host "Creating backup archive..." -ForegroundColor $Colors.Info
    
    $inventoryDir = Get-Item $InventoryPath -ErrorAction SilentlyContinue
    if ($null -eq $inventoryDir) {
        Write-Host "⚠️  No inventory directory to archive" -ForegroundColor $Colors.Warning
        return $false
    }
    
    try {
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $archiveName = "teams-config-inventory-$timestamp.zip"
        
        $files = Get-ChildItem -Path "inventory" -File -Recurse
        
        if ($files.Count -eq 0) {
            Write-Host "No files to archive" -ForegroundColor $Colors.Warning
            return $false
        }
        
        # Create zip
        if (Test-Path $archiveName) {
            Remove-Item $archiveName -Force
        }
        
        $zip = [System.IO.Compression.ZipFile]::Open($archiveName, 'Create')
        
        foreach ($file in $files) {
            $entryName = $file.FullName.Replace((Get-Location).Path + '\', '').Replace('\', '/')
            [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, $file.FullName, $entryName) | Out-Null
        }
        
        $zip.Dispose()
        
        $size = (Get-Item $archiveName).Length
        Write-Host "✓ Archive created: $archiveName ($([int]($size / 1024)) KB)" -ForegroundColor $Colors.Success
        
        return $true
    } catch {
        Write-Host "⚠️  Could not create archive: $_" -ForegroundColor $Colors.Warning
        return $false
    }
}

function Show-Summary {
    Write-Header "Inventory Export Summary"
    
    $inventoryDir = Get-Item $InventoryPath -ErrorAction SilentlyContinue
    
    if ($null -eq $inventoryDir) {
        Write-Host "No inventory directory found" -ForegroundColor $Colors.Warning
        return
    }
    
    $files = @(Get-ChildItem -Path $InventoryPath -File)
    
    if ($files.Count -eq 0) {
        Write-Host "No files exported" -ForegroundColor $Colors.Warning
        return
    }
    
    Write-Host ""
    Write-Host "📁 Exported $($files.Count) files to inventory/:" -ForegroundColor $Colors.Info
    Write-Host ""
    
    $totalSize = 0
    $files | Sort-Object Name | ForEach-Object {
        $size = $_.Length
        $totalSize += $size
        
        $icon = switch ($_.Extension) {
            ".md"   { "📄" }
            ".json" { "📋" }
            ".zip"  { "📦" }
            ".csv"  { "📊" }
            default { "📄" }
        }
        
        Write-Host "  $icon $($_.Name.PadRight(40)) $($size.ToString('N0').PadLeft(12)) bytes"
    }
    
    Write-Host ""
    Write-Host "  Total size: $($totalSize.ToString('N0')) bytes" -ForegroundColor $Colors.Info
    
    Write-Host ""
    Write-Host "📖 Main Documentation: inventory/teams-config-inventory.md" -ForegroundColor $Colors.Success
    
    Write-Host ""
    Write-Host "⚠️  Next Steps:" -ForegroundColor $Colors.Warning
    Write-Host "  1. Review: inventory/teams-config-inventory.md"
    Write-Host "  2. Manually add Teams PowerShell exports:"
    Write-Host "     - Connect-MicrosoftTeams"
    Write-Host "     - Get-CsTeamsAppSetupPolicy | ConvertTo-Json | Out-File ..."
    Write-Host "  3. Commit to git:"
    Write-Host "     git add inventory/"
    Write-Host "     git commit -m 'docs: export Teams configuration'"
}

# Main execution
try {
    Push-Location $RepoRoot
    # Archive only mode
    if ($ArchiveOnly) {
        New-InventoryArchive
        return
    }
    
    # Check prerequisites unless skipped
    if (-not $SkipChecks) {
        $prereqPass = Test-Prerequisites
        
        if (-not $prereqPass) {
            Write-Host ""
            Write-Host "⚠️  Some prerequisites are missing (see above)" -ForegroundColor $Colors.Warning
            
            if (-not $CheckOnly) {
                $response = Read-Host "Continue anyway? (y/n)"
                if ($response -ne 'y' -and $response -ne 'Y') {
                    exit 1
                }
            }
        }
        
        $envPass = Test-EnvironmentVariables
        
        if (-not $envPass) {
            Write-Host ""
            Write-Host "⚠️  Some environment variables need to be configured" -ForegroundColor $Colors.Warning
            
            if (-not $CheckOnly) {
                $response = Read-Host "Continue with partial configuration? (y/n)"
                if ($response -ne 'y' -and $response -ne 'Y') {
                    exit 1
                }
            }
        }
    }
    
    if ($CheckOnly) {
        Write-Host ""
        Write-Host "✓ Prerequisite check complete" -ForegroundColor $Colors.Success
        return
    }
    
    # Run inventory
    $success = Start-InventoryAudit
    
    if (-not $success) {
        Write-Host ""
        Write-Host "❌ Inventory failed. Check output above for errors." -ForegroundColor $Colors.Error
        exit 1
    }
    
    # Create archive
    New-InventoryArchive
    
    # Show summary
    Show-Summary
    
    Write-Host ""
    Write-Host "✓ Inventory complete!" -ForegroundColor $Colors.Success
    Write-Host ""
    
} catch {
    Write-Host ""
    Write-Host "Fatal error: $_" -ForegroundColor $Colors.Error
    exit 1
} finally {
    Pop-Location
}
