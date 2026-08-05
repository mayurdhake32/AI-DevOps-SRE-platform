# AWS Troubleshooting Guide

## EC2 Instance Unreachable

### Symptoms
- SSH connection timeout
- Instance Status Checks failing
- Public IP not responding

### Diagnosis
```bash
# Check instance status
aws ec2 describe-instance-status --instance-ids i-1234567890abcdef0

# Check security group rules
aws ec2 describe-security-groups --group-ids sg-xxxxxxxx

# Verify VPC routing
aws ec2 describe-route-tables --filters Name=vpc-id,Values=vpc-xxxxxx
```

### Fixes
1. **Security Group**: Ensure port 22 (SSH) or 3389 (RDP) is open to your IP
2. **NACL**: Check Network ACL rules aren't blocking traffic
3. **Route Table**: Verify Internet Gateway route exists for public subnets
4. **Instance Profile**: Check IAM role has necessary permissions
5. **User Data**: Review `/var/log/cloud-init-output.log` for bootstrap errors

## S3 Access Denied

### Error
```
AccessDenied: Access Denied
status code: 403
```

### Fixes
1. Check bucket policy doesn't explicitly deny
2. Verify IAM policy allows `s3:GetObject` or `s3:PutObject`
3. Check object ACL if bucket is private
4. Ensure KMS key permissions if using SSE-KMS
5. Verify requester pays isn't enabled

## RDS Connection Issues

### Error
```
FATAL: no pg_hba.conf entry for host
```

### Fixes
1. Add client IP to RDS security group
2. Check VPC peering if cross-VPC
3. Verify DB is publicly accessible (if needed)
4. Check parameter group for `rds.force_ssl`
5. Review connection limits: `max_connections`

## Lambda Timeout

### Symptoms
- Task timed out after 30.03 seconds
- Function exits without completing

### Fixes
1. Increase timeout in function configuration (max 15 min)
2. Check for infinite loops or blocking calls
3. Use async patterns for long operations
4. Optimize cold start: reduce deployment package size
5. Increase memory allocation (also increases CPU)

## IAM Permission Issues

### Error
```
User: arn:aws:iam::123456789:user/ci-cd is not authorized to perform: 
sts:AssumeRole on resource: arn:aws:iam::987654321:role/DeployRole
```

### Fixes
1. Add trust relationship to role allowing account to assume
2. Attach policy with `sts:AssumeRole` permission to user
3. Check for external ID requirement in trust policy
4. Verify MFA isn't required but not provided
