# Linux System Administration

## Disk Space Full

### Diagnosis
```bash
df -h
du -sh /var/log/* | sort -rh | head -10
ncdu /          # interactive disk usage analyzer
```

### Fixes
```bash
# Clean package cache
sudo apt-get clean
sudo yum clean all

# Rotate logs
sudo logrotate -f /etc/logrotate.conf

# Find large files
sudo find / -type f -size +100M -exec ls -lh {} \;

# Clean Docker
sudo docker system prune -a --volumes

# Clean old kernels
sudo apt-get autoremove --purge
```

## High CPU Usage

### Diagnosis
```bash
top -o %CPU
ps aux --sort=-%cpu | head -20
perf top
```

### Fixes
1. Identify process: `pidstat -u 1`
2. Check for runaway scripts or infinite loops
3. Limit with `nice` or `cpulimit`
4. Scale horizontally if legitimate load
5. Check for cryptominers: unexpected high CPU + network

## Memory Issues

### Diagnosis
```bash
free -h
vmstat 1 5
cat /proc/meminfo
smem -r
```

### OOM Killer
```bash
# Check OOM kills
dmesg | grep -i "killed process"
journalctl -k | grep -i "oom"
```

### Fixes
1. Add swap: `sudo fallocate -l 2G /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile`
2. Find memory leaks: `valgrind --leak-check=full ./app`
3. Reduce application memory limits
4. Enable OOM score adjustment for critical services

## SSH Connection Issues

### Error
```
Connection refused
Connection timed out
Permission denied (publickey)
```

### Fixes
```bash
# Check SSH service
sudo systemctl status sshd

# Verify key permissions
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_rsa
chmod 644 ~/.ssh/id_rsa.pub

# Debug connection
ssh -vvv user@host

# Check auth logs
sudo tail -f /var/log/auth.log
```

## Process Won't Die

```bash
# Find process
pgrep -f "process_name"

# Kill gracefully
kill -15 <pid>

# Force kill
kill -9 <pid>

# Kill by name
sudo pkill -9 process_name
```

## Cron Jobs Not Running

### Diagnosis
```bash
crontab -l
sudo cat /var/log/syslog | grep CRON
cat /var/spool/mail/$USER
```

### Common Fixes
1. Use absolute paths in cron
2. Set environment variables: `SHELL=/bin/bash`, `PATH=...`
3. Redirect output: `* * * * * /script.sh >> /var/log/script.log 2>&1`
4. Check cron service: `sudo systemctl status cron`
