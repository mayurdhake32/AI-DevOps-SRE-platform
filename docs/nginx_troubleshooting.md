# Nginx Troubleshooting

## 502 Bad Gateway

### Causes
- Upstream server down
- Upstream timeout
- Wrong upstream port

### Fix
```nginx
location /api/ {
    proxy_pass http://backend:8080;
    proxy_connect_timeout 30s;
    proxy_send_timeout 30s;
    proxy_read_timeout 30s;
}
```

## 504 Gateway Timeout

### Fix
```nginx
proxy_read_timeout 300;
proxy_connect_timeout 300;
proxy_send_timeout 300;
```

## SSL Certificate Issues

### Error
```
SSL: error:14094418:SSL routines:ssl3_read_bytes:tlsv1 alert unknown ca
```

### Fix
```bash
# Check certificate chain
openssl s_client -connect example.com:443 -servername example.com

# Verify cert expiry
openssl x509 -in cert.pem -noout -dates

# Renew with certbot
sudo certbot renew --dry-run
```

## Rate Limiting

```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

location /api/ {
    limit_req zone=api burst=20 nodelay;
    proxy_pass http://backend;
}
```

## High Memory Usage

### Fix
```nginx
# Reduce worker connections
worker_connections 1024;

# Enable gzip
gzip on;
gzip_types application/json text/css;

# Cache static files
location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```
