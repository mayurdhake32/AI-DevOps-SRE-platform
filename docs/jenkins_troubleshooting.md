# Jenkins Troubleshooting

## Build Hanging

### Causes
- Waiting for input (pipeline input step)
- Deadlocked resource
- Network timeout

### Fix
```groovy
// Add timeout to pipeline
pipeline {
    options {
        timeout(time: 30, unit: 'MINUTES')
    }
}
```

## Agent Offline

### Fix
1. Check agent service: `sudo systemctl status jenkins-agent`
2. Verify JNLP port is open (default 50000)
3. Re-launch agent from Jenkins UI
4. Check agent logs: `~/jenkins-agent/remoting/logs/`

## Plugin Dependency Issues

### Error
```
Failed to load: Git plugin (1.0)
- Update required: Credentials plugin (2.0) to be updated to 2.1
```

### Fix
1. Update all plugins from Manage Jenkins → Manage Plugins
2. Restart Jenkins after plugin updates
3. If stuck: manually delete plugin `.hpi` from `$JENKINS_HOME/plugins`

## Disk Space Full

```bash
# Clean old builds
find $JENKINS_HOME/jobs/ -name builds -type d | xargs -I {} find {} -maxdepth 1 -mtime +30 -type d

# Clean workspace
find $JENKINS_HOME/workspace/ -maxdepth 1 -mtime +7 -type d

# Archive old logs
```

## Pipeline Syntax Errors

### Common Mistakes
```groovy
// WRONG: Missing agent
pipeline {
    stages { ... }
}

// CORRECT
pipeline {
    agent any
    stages { ... }
}
```

### Validate Pipeline
```bash
# Using Jenkins CLI
java -jar jenkins-cli.jar declarative-linter < Jenkinsfile
```
