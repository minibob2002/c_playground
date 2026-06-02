$ErrorActionPreference = "Stop"

$repoRoot = git rev-parse --show-toplevel
if (-not $repoRoot) {
    throw "Run this script inside the assignment Git repository."
}

$hookDir = Join-Path $repoRoot ".git/hooks"
$hookPath = Join-Path $hookDir "pre-commit"

@'
#!/bin/sh
if [ -z "$ASSIGNMENT_COMMIT_WRAPPER" ]; then
  echo "Use the assignment commit wrapper so AI metadata and quiz answers are recorded:"
  echo "  python tools/assignment_commit.py"
  exit 1
fi
'@ | Set-Content -Path $hookPath -Encoding ascii

Write-Host "Installed assignment pre-commit hook at $hookPath"
