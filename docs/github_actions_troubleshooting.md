# GitHub Actions Troubleshooting

## Workflow Not Triggering

### Common Causes
1. YAML syntax error in `.github/workflows/*.yml`
2. Branch filter mismatch (`on.push.branches`)
3. Path filter excluding changed files
4. Workflow disabled in repository settings

### Fixes
```yaml
# Correct trigger
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
```

## Action Failed: Permission Denied

### Error
```
Error: Resource not accessible by integration
```

### Fixes
1. Go to Settings → Actions → General → Workflow permissions
2. Change to "Read and write permissions"
3. Or add `permissions` block to workflow:
```yaml
permissions:
  contents: write
  pull-requests: write
```

## Secrets Not Available

### Error
```
Error: Input required and not supplied: GITHUB_TOKEN
```

### Fixes
1. For `GITHUB_TOKEN`: it's auto-generated, just reference it
2. For custom secrets: Settings → Secrets and variables → Actions
3. Secrets are NOT available to workflows triggered by forks
4. Use `secrets.GITHUB_TOKEN` not `env.GITHUB_TOKEN`

## Docker Build Push Failed

### Error
```
denied: requested access to the resource is denied
unauthorized: authentication required
```

### Fixes
```yaml
- name: Login to Docker Hub
  uses: docker/login-action@v3
  with:
    username: ${{ secrets.DOCKER_USERNAME }}
    password: ${{ secrets.DOCKER_PASSWORD }}
```

## Cache Not Working

### Fix
```yaml
- uses: actions/cache@v3
  with:
    path: |
      ~/.npm
      ~/.m2
      ~/.gradle
    key: ${{ runner.os }}-build-${{ hashFiles('**/package-lock.json') }}
```

## Self-Hosted Runner Offline

### Diagnosis
```bash
# On runner machine
cd ~/actions-runner
./svc.sh status

# Check logs
tail -f ~/actions-runner/_diag/*.log
```

### Fixes
1. Restart service: `sudo ./svc.sh start`
2. Re-run config if token expired: `./config.sh --url ... --token ...`
3. Check network connectivity to GitHub
4. Verify runner isn't disabled in repository settings
