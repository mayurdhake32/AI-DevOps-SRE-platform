# SSL/TLS Troubleshooting

## Certificate Expired

### Diagnosis
```bash
# Check expiry
openssl x509 -in cert.pem -noout -dates

# Check remotely
echo | openssl s_client -servername example.com -connect example.com:443 2>/dev/null | openssl x509 -noout -dates
```

### Fix
```bash
# Renew with certbot
sudo certbot renew

# Or generate new cert
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout key.pem -out cert.pem
```

## Certificate Chain Incomplete

### Diagnosis
```bash
# Test SSL Labs: https://www.ssllabs.com/ssltest/
# Or locally:
openssl s_client -connect example.com:443 -showcerts
```

### Fix
```bash
# Combine intermediate + root
cat server.crt intermediate.crt root.crt > bundle.crt

# Nginx config
ssl_certificate /etc/ssl/bundle.crt;
ssl_certificate_key /etc/ssl/server.key;
```

## TLS Version Mismatch

### Error
```
SSLHandshakeException: Received fatal alert: protocol_version
```

### Fix
```bash
# Check supported versions
openssl s_client -connect example.com:443 -tls1_2

# Update client to support TLS 1.2+
# Or configure server to accept older versions (not recommended)
```

## Self-Signed Certificate in Chain

### Fix
```bash
# Trust the CA certificate
sudo cp ca.crt /usr/local/share/ca-certificates/
sudo update-ca-certificates

# Or skip verification (DEV ONLY)
curl -k https://example.com
```

## HSTS Issues

### Fix
```nginx
# Remove HSTS header temporarily
add_header Strict-Transport-Security "";

# Or clear browser HSTS cache
# Chrome: chrome://net-internals/#hsts
```
