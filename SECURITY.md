# QRVault Security Documentation

## Threat Model

QRVault assumes:
- The server is trusted for storage and access control
- The client browser is trusted for encryption/decryption
- An attacker may intercept network traffic
- An attacker may attempt brute-force on share tokens
- An attacker may try to access files after expiration

## Encryption Model

### File Encryption
- Algorithm: AES-256-GCM (Galois/Counter Mode)
- Key size: 256 bits
- IV size: 96 bits (12 bytes)
- Key generation: Web Crypto API `crypto.subtle.generateKey()`
- Mode: Authenticated encryption (provides confidentiality and integrity)

### Key Handling
- AES key generated client-side using `window.crypto.subtle.generateKey()`
- Key exported as raw Base64 and stored in URL fragment (`#key`)
- URL fragments are NOT sent to server in HTTP requests
- Server never receives, stores, or logs the encryption key
- Each share gets a unique encryption key

### Key Wrapping (Optional RSA)
- RSA-OAEP can be used for key exchange demonstrations
- AES-256-GCM remains primary for bulk file encryption
- RSA is slower for large files; symmetric encryption is standard practice

## Token Security

### Share Token
- Generated using `secrets.token_urlsafe(32)` (256 bits of randomness)
- Stored as SHA-256 hash in database
- Raw token only present in share URL
- Brute-force infeasible: 2^256 possibilities

### Management Token
- Separate token for uploader management
- Also 256 bits, stored as SHA-256 hash
- Required for revoke/delete operations

## Access Control

Token-based access control:
1. Valid token + not expired + not revoked + under download limit = Access
2. Any condition failure = Access denied
3. All checks performed server-side
4. No client-side-only access control

## File Storage

### Encrypted Storage
- Files stored with random UUID-based filenames (e.g., `f83c1e9a...enc`)
- Original filenames sanitized and stored in database only
- Storage directory not exposed via static file serving
- Files served only through authenticated backend routes

### Path Traversal Protection
- `safe_path()` validates resolved path stays within storage directory
- Filename sanitization removes `..`, `/`, `\` characters

## Expiration

- Expiration time set at share creation
- Server-side validation on every access attempt
- Expired shares marked in database
- Cleanup service removes expired files after retention period
- Not reliant on client-side countdown

## Download Limits

- Limit set at share creation (1, 3, 5, 10, 25, 50)
- Server increments count on each authorized download
- When limit reached, status updated to `limit_reached`
- Subsequent download attempts rejected server-side

## Rate Limiting

In-memory rate limiting:
- Upload: 30 requests/hour per IP
- Download: 60 requests/hour per IP
- Share access: 100 requests/hour per IP

## Security Headers

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Content-Security-Policy` (restrictive)
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Cache-Control: no-store, no-cache`

## Audit Logging

Logged events:
- Share created
- Share accessed
- Download authorized
- Download completed
- Download rejected
- Share revoked
- Share expired
- File deleted

NOT logged:
- File contents
- Encryption keys
- URL fragments (passwords)
- Plaintext passwords

## Password Protection

- Optional feature
- Password hashed with SHA-256 before storage
- Hash stored in database (not plaintext)
- Verified server-side before download authorization

## Known Limitations

1. **No HTTPS in development**: Production deployment requires HTTPS
2. **In-memory rate limiting**: Resets on server restart
3. **Single-server deployment**: Not distributed
4. **No file integrity after upload**: Cannot verify encrypted file wasn't corrupted
5. **SQLite limitations**: Not suitable for high-concurrency production
6. **Client-side encryption trust**: Relies on browser's Web Crypto API

## Deployment Security

For production:
1. Use HTTPS (TLS 1.3 recommended)
2. Set strong `SECRET_KEY` environment variable
3. Configure proper file permissions on storage directory
4. Use a production WSGI server (Gunicorn, uWSGI)
5. Place behind reverse proxy (Nginx, Apache)
6. Regular database backups
7. Monitor audit logs
8. Set appropriate `MAX_FILE_SIZE`
9. Configure CORS policies if needed
10. Enable HSTS in production
