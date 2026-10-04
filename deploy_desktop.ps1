# deploy_desktop.ps1 - Synchronizes and deploys standalone game to Desktop
$ErrorActionPreference = "Stop"

$workspaceRoot = $PSScriptRoot
Write-Host "Workspace Root: $workspaceRoot"

$distDir = Join-Path $workspaceRoot "dist\CognitiveMaze"
if (!(Test-Path $distDir)) {
    throw "dist\CognitiveMaze does not exist. Please run PyInstaller first."
}

# 1. Sync assets, db, datasets, layout_config.json to dist\CognitiveMaze
Write-Host "Syncing runtime assets to dist\CognitiveMaze..."
Copy-Item -Path (Join-Path $workspaceRoot "assets") -Destination (Join-Path $distDir "assets") -Recurse -Force
Copy-Item -Path (Join-Path $workspaceRoot "db") -Destination (Join-Path $distDir "db") -Recurse -Force
Copy-Item -Path (Join-Path $workspaceRoot "datasets") -Destination (Join-Path $distDir "datasets") -Recurse -Force
Copy-Item -Path (Join-Path $workspaceRoot "layout_config.json") -Destination (Join-Path $distDir "layout_config.json") -Force

# 2. Identify Desktop folder
$desktop = [Environment]::GetFolderPath("Desktop")
if ([string]::IsNullOrWhiteSpace($desktop)) {
    $desktop = Join-Path $env:USERPROFILE "Desktop"
}
$targetDir = Join-Path $desktop "Cognitive Maze"

Write-Host "Target Desktop Directory: $targetDir"
if (Test-Path $targetDir) {
    Write-Host "Cleaning existing desktop directory: $targetDir"
    Remove-Item -Path $targetDir -Recurse -Force
}
New-Item -ItemType Directory -Path $targetDir -Force | Out-Null

# 3. Copy dist\CognitiveMaze files to Desktop
Write-Host "Copying standalone distribution files to Desktop\Cognitive Maze..."
Copy-Item -Path "$distDir\*" -Destination $targetDir -Recurse -Force

# Also check non-OneDrive Desktop if different
$legacyDesktop = Join-Path $env:USERPROFILE "Desktop"
if ((Test-Path $legacyDesktop) -and ($legacyDesktop -ne $desktop)) {
    $legacyTargetDir = Join-Path $legacyDesktop "Cognitive Maze"
    Write-Host "Mirroring to user Desktop: $legacyTargetDir"
    if (Test-Path $legacyTargetDir) {
        Remove-Item -Path $legacyTargetDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $legacyTargetDir -Force | Out-Null
    Copy-Item -Path "$distDir\*" -Destination $legacyTargetDir -Recurse -Force
}

# 4. Create Desktop Shortcut
$exePath = Join-Path $targetDir "CognitiveMaze.exe"
$lnkPath = Join-Path $desktop "Cognitive Maze.lnk"
$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($lnkPath)
$shortcut.TargetPath = $exePath
$shortcut.WorkingDirectory = $targetDir
$shortcut.Description = "Cognitive Maze - Standalone Educational Math Adventure Game"
$shortcut.Save()

Write-Host "[SUCCESS] Standalone game ready at: $targetDir"
Write-Host "[SUCCESS] Executable: $exePath"
Write-Host "[SUCCESS] Shortcut created at: $lnkPath"
