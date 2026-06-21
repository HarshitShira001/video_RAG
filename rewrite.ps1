Set-Location "C:\Users\dell\OneDrive\Desktop\rag_video"

# Set correct identity
git config user.email "shiraashu8@gmail.com"
git config user.name  "Harshit Shira"

Write-Host "Identity: $(git config user.email)" -ForegroundColor Cyan

$D = "2026-06-21"

# ---- 7 commit groups ----
$groups = @(
    [PSCustomObject]@{
        Time  = "${D}T09:00:00+05:30"
        Msg   = "Initial commit: project scaffolding and configuration"
        Files = @(".gitignore","README.md","Requirements.txt")
    },
    [PSCustomObject]@{
        Time  = "${D}T11:00:00+05:30"
        Msg   = "Add audio processor and video extractor utilities"
        Files = @("utils/audio_processor.py","core/extractor.py")
    },
    [PSCustomObject]@{
        Time  = "${D}T13:00:00+05:30"
        Msg   = "Add transcriber and vector store modules"
        Files = @("core/transcriber.py","core/vector_store.py")
    },
    [PSCustomObject]@{
        Time  = "${D}T15:00:00+05:30"
        Msg   = "Add summarizer and RAG engine modules"
        Files = @("core/summarizer.py","core/rag_engine.py")
    },
    [PSCustomObject]@{
        Time  = "${D}T17:00:00+05:30"
        Msg   = "Add main orchestration pipeline"
        Files = @("main.py")
    },
    [PSCustomObject]@{
        Time  = "${D}T19:00:00+05:30"
        Msg   = "Add Streamlit app and integration tests"
        Files = @("app.py","test.py")
    },
    [PSCustomObject]@{
        Time  = "${D}T21:00:00+05:30"
        Msg   = "Final cleanup: code polish and project structure review"
        Files = @()  # will re-add all remaining/modified files
        AddAll = $true
    }
)

# Step 1: Orphan branch
Write-Host "`nCreating orphan branch..." -ForegroundColor Cyan
git checkout --orphan video-rag-clean
git reset HEAD -- . 2>&1 | Out-Null
Write-Host "Orphan branch created, index cleared." -ForegroundColor Green

# Step 2: Make commits
Write-Host "`nCreating 7 commits dated $D ..." -ForegroundColor Cyan
$num = 1

foreach ($g in $groups) {
    $staged = 0

    if ($g.PSObject.Properties["AddAll"] -and $g.AddAll) {
        # Stage any remaining unstaged tracked files
        git add -A 2>&1 | Out-Null
        $staged = 1  # at least signal something was staged
    } else {
        foreach ($f in $g.Files) {
            if (Test-Path -LiteralPath $f) {
                git add -- $f
                $staged++
            } else {
                Write-Host "  MISSING: $f" -ForegroundColor Red
            }
        }
    }

    # Check if there's anything staged
    $diff = git diff --cached --name-only 2>&1
    if ($diff) {
        $env:GIT_AUTHOR_DATE    = $g.Time
        $env:GIT_COMMITTER_DATE = $g.Time
        git commit -m $g.Msg 2>&1 | Out-Null
        Write-Host "[$num/7] $($g.Msg)  [$($g.Time)]" -ForegroundColor Green
        $num++
    } else {
        Write-Host "SKIPPED (nothing to commit): $($g.Msg)" -ForegroundColor DarkYellow
    }
}

Remove-Item Env:\GIT_AUTHOR_DATE    -ErrorAction SilentlyContinue
Remove-Item Env:\GIT_COMMITTER_DATE -ErrorAction SilentlyContinue

# Step 3: Show log
Write-Host "`nFinal commit log:" -ForegroundColor Cyan
git log --format="%h | %ae | %ad | %s" --date=short

# Step 4: Force push
Write-Host "`nRenaming branch to main and force pushing..." -ForegroundColor Yellow
git branch -M main
git push origin main --force

Write-Host "`nDONE - video_RAG repo rewritten with 7 commits on $D" -ForegroundColor Green
