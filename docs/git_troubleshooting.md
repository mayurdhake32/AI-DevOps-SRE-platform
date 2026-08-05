# Git Troubleshooting

## Merge Conflicts

### Fix
```bash
# See conflicted files
git diff --name-only --diff-filter=U

# Resolve manually, then
git add <resolved-files>
git commit  # Use default merge message

# Or abort
git merge --abort
```

## Large File Accidentally Committed

### Fix
```bash
# Install git-lfs
git lfs install
git lfs track "*.psd"
git add .gitattributes

# For already committed large files
git filter-repo --strip-blobs-bigger-than 10M
# Or use BFG Repo-Cleaner
```

## Detached HEAD

### Fix
```bash
# Save changes to new branch
git checkout -b temp-branch

# Or go back to main
git checkout main

# If you made commits in detached HEAD
git checkout main
git cherry-pick <commit-hash>
```

## Push Rejected

### Error
```
! [rejected]        main -> main (fetch first)
```

### Fix
```bash
# Pull first
git pull origin main --rebase

# Then push
git push origin main

# Force push (DANGEROUS - only if sure)
git push origin main --force-with-lease
```

## Submodules Not Updating

```bash
# Initialize and update
git submodule update --init --recursive

# Force update
git submodule update --remote --merge
```

## Credential Issues

```bash
# Cache credentials
git config --global credential.helper cache

# Or use SSH instead of HTTPS
git remote set-url origin git@github.com:user/repo.git
```
