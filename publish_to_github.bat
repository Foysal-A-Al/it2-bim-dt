@echo off
REM Creates a new GitHub repository "it2-bim-dt" under your account and pushes this folder.
REM Needs Git (git-scm.com) and the GitHub CLI (cli.github.com). Log in once with:  gh auth login
where git >nul 2>nul || (echo Git not found. Install it from https://git-scm.com and try again. & exit /b 1)
where gh  >nul 2>nul || (echo GitHub CLI not found. Install it from https://cli.github.com and try again. & exit /b 1)
gh auth status >nul 2>nul || gh auth login
if not exist .git (
  git init -b main
  git add .
  git commit -m "IT2: identity and topology integrity for BIM-based digital twins"
)
gh repo create it2-bim-dt --public --source . --remote origin --push --description "Identity and topology integrity checks for BIM-based digital twins (paper code, data pointers and desktop app)"
echo.
echo Done. Your repository:
gh repo view --json url -q .url
