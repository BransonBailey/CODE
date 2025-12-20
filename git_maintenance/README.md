# Git Maintenance Guide

This document is a quick reference for maintaining Git repositories in my `CODE/` directory on Pop!_OS / Linux.

It covers daily usage, cleanup, fixing mistakes, syncing with GitHub, and keeping repositories healthy.

---

## 📍 Daily Commands

### Check repository status
```bash
git status
```

Shows:
- modifed files
- staged files
- untracked files

### View commit history
```bash
git log --oneline --graph --decorate
```

### See file changes
```bash
git diff
```
Staged changes only:
```bash
git diff --staged
```

## 🧹 Cleaning & Fixing Mistakes

### Unstage a file (keep changes)
```bash
git restore --staged <file>
```

### Discard local changes (⚠️ irreversible)
```bash
git restore <file>
```

### Remove untracked files
Preview first:
```bash
git clean -n
```

Delete
```bash
git clean -f
```

## 🔄 Syncing with GitHub
### Pull latest changes
```bash
git pull
```

### Push local commits
``` git push
```

### Check remote repositories
``` git remote -v
```

## 🌱 Branch Management
### List branches
``` bash
git branch
```

### Create and switch to a new branch
```bash
git switch -c <branch-name>
```

### Switch branches
```bash
git switch main
```

### Delete a local branch
``` bash
git branch -d <branch-name>
```

## 🧠 Undoing Commits
### Undo last commit (keep changes)
```bash
git reset --soft HEAD~1
```

### Undo last commit and discard changes (⚠️ dangerous)
```bash
git reset --hard HEAD~1
```

### Edit last commit message
```bash
git commit --amend
```

## 🧼 Repository Health
### Optimize repository
```bash
git gc
```

### Verify repository integrity
```bash
git fsck
```

## 🗂️ .gitignore Maintenance

Common entries:
```bash
node_modules/
.env
__pycache__/
*.log
.DS_Store
```

If .gitignore is updated after files were tracked:
```bash
git rm -r --cached .
git add .
git commit -m "Update .gitignore"
```

## 🚨 Recovery & Safety
View reference log (Git time machine)
```bash
git reflog
```

Use this to recover lost commits or undo bad resets.

## ⭐ Helpful Aliases

Configured once:
```bash
git config --global alias.st status
git config --global alias.lg "log --oneline --graph --decorate"
```

Usage:
```bash
git st
git lg
```

## ✅ Quick Pre-Push Checklist
```bash
git status
git diff --stat
git log -1
```

If everything looks good — push.
