# QRVault

**Secure QR-Based File Sharing Platform**

A cybersecurity project implementing end-to-end encrypted file sharing with QR codes, expiring links, and access controls.

## Overview

QRVault allows users to securely share files through encrypted uploads, QR code generation, and token-based access control. Files are encrypted client-side using AES-256-GCM before upload, and decryption happens locally in the receiver's browser. The server never has access to plaintext files or encryption keys.

## Project Objective

"Build a secure P2P or cloud-based file sharing platform with end-to-end encryption, expiring links, and access controls."

## Key Features

- **Client-Side AES-256-GCM Encryption**: Files encrypted in browser before upload
- **QR Code Sharing**: Generate QR codes containing secure share URLs
- **Expiring Links**: Server-enforced expiration (5 minutes to 24 hours)
- **Download Limits**: Configurable maximum download count (1-50)
- **Instant Revocation**: Revoke access to shared files at any time
- **Password Protection**: Optional password layer for extra security
- **No Account Required**: Token-based access control, no registration needed
- **Audit Logging**: All access attempts logged for security monitoring
- **Security Headers**: CSP, X-Frame-Options, nosniff, and more
- **Rate Limiting**: Protection against brute-force and abuse

## Architecture

```
QRVault/
├── app.py                    # Flask application factory
├── config.py                 # Configuration management
├── database/
│   ├── db.py                # SQLite database setup
│   └── models.py            # Data models (Share, AuditLog)
├── routes/
│   ├── main.py              # Landing page routes
│   ├── upload.py            # File upload API
│   ├── sharing.py           # Share page routes
│   └── api.py               # Download/management API
├── security/
│   ├── tokens.py            # Secure token generation
│   ├── validation.py        # Input validation
│   ├── rate_limit.py        # Rate limiting
│   └── headers.py           # Security headers
├── services/
│   ├── file_service.py      # File storage operations
│   ├── cleanup_service.py   # Expired file cleanup
│   └── qr_service.py        # QR code generation
├── static/
│   ├── css/style.css        # Application styles
│   └── js/
│       ├── encryption.js    # Web Crypto API encryption
│       ├── upload.js        # Upload workflow
│       └── share.js         # Download workflow
├── templates/               # Jinja2 HTML templates
├── storage/encrypted/       # Encrypted file storage
└── tests/                   # Pytest test suite
```

## How It Works

### Upload Flow
1. User selects a file
2. Browser generates AES-256-GCM key
3. Browser encrypts file locally
4. Encrypted file uploaded to server
5. Server generates share token + QR code
6. Encryption key stored in URL fragment (#key)

### Download Flow
1. Receiver scans QR code
2. Browser loads share page
3. Receiver clicks "Download Securely"
4. Browser downloads encrypted ciphertext
5. Browser extracts key from URL fragment
6. Browser decrypts file locally
7. Original file saved to receiver's device

## Encryption Design

### Why AES-256-GCM?
- **Authenticated Encryption**: Provides both confidentiality and integrity
- **Performance**: Hardware-accelerated on modern CPUs
- **Standard**: Widely supported and well-analyzed
- **Bulk Encryption**: Efficient for large files (vs RSA)

### Key Management
- 256-bit AES key generated per share via Web Crypto API
- Key stored in URL fragment (not sent to server)
- Each share has unique key
- Server never accesses the key

### URL Fragment Security
```
https://example.com/share/TOKEN#BASE64_AES_KEY
```
- Fragment (#) is NOT sent in HTTP requests
- Server only receives `/share/TOKEN`
- Key stays in browser only

## QR Sharing Workflow

1. Upload encrypted file
2. Server returns share URL + QR image
3. QR contains: `https://domain/share/TOKEN`
4. Receiver scans QR → opens share page
5. Receiver downloads → browser decrypts with `#key`

## Access Control

Token-based access control with multiple layers:
- **Random Token**: 256-bit cryptographically secure
- **Expiration**: Server-enforced time limit
- **Download Limit**: Maximum download count
- **Revocation**: Instant access revocation
- **Password**: Optional password protection

## Technology Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.x, Flask |
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| Database | SQLite |
| Encryption | Web Crypto API (AES-256-GCM) |
| QR Code | qrcode Python library |
| Security | secrets, hashlib, Werkzeug |

## Installation

### Prerequisites
- Python 3.8+
- pip

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/QRVault.git
cd QRVault

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -c "from database.db import init_db; init_db()"
```

## Configuration

### Environment Variables

```bash
# .env file
SECRET_KEY=your-secret-key-here
DATABASE_URL=instance/qrvault.db
STORAGE_PATH=storage/encrypted
MAX_FILE_SIZE=52428800  # 50MB in bytes
```

### See `.env.example` for all options.

## Running Locally

```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Usage

### Share a File
1. Navigate to `/upload`
2. Select or drag-drop a file
3. Configure expiry time and download limit
4. Click "Encrypt & Generate Secure Share"
5. Share the QR code or secure link

### Receive a File
1. Scan QR code or open share link
2. Review file details
3. Click "Download Securely"
4. Accept the download confirmation
5. Browser decrypts and saves the file

### Manage a Share
1. Use the management link from upload
2. View QR code, link, and stats
3. Revoke access or delete share

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_upload.py -v

# Run with coverage
pytest tests/ -v --tb=short
```

### Test Coverage
- Upload validation
- Share creation
- Token access control
- Expiration enforcement
- Download limit enforcement
- Revocation
- Filename sanitization
- Security headers
- Rate limiting

## Security Considerations

- Files encrypted client-side before upload
- Server never accesses plaintext files or keys
- Tokens are 256-bit cryptographically secure
- All access control validated server-side
- Rate limiting on all endpoints
- Security headers on all responses
- Audit logging for all operations
- Expired files cleaned up automatically

## Limitations

- Single-server deployment (not distributed)
- In-memory rate limiting (resets on restart)
- Requires HTTPS for production use
- Trusts client browser for encryption
- SQLite not suitable for high concurrency

## Future Enhancements

- [ ] End-to-end RSA key exchange
- [ ] File chunking for large files
- [ ] Persistent rate limiting (Redis)
- [ ] User accounts for file management
- [ ] Multi-file sharing
- [ ] File preview before download
- [ ] Webhook notifications
- [ ] API key authentication
- [ ] Docker deployment
- [ ] Kubernetes orchestration

## Internship Requirement Mapping

| Requirement | QRVault Implementation |
|-------------|----------------------|
| Secure File Sharing | Encrypted file upload/download |
| End-to-End Encryption | Client-side AES-256-GCM encryption |
| Expiring Links | Server-side expiration validation |
| Access Controls | Token-based, download limits, revocation |
| Secure Communication | HTTPS recommended for deployment |
| File Encryption | AES-256-GCM |
| Python | Flask backend |
| RSA/AES | AES primary, RSA optional for key wrapping |

## Disclaimer

QRVault is an educational cybersecurity project developed for internship requirements. Use it only for files and systems you are authorized to manage. The developers assume no responsibility for misuse.

## License

MIT License - See LICENSE file for details.
