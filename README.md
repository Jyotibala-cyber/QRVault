<div align="center">

# 🛡️ QRVault

### Secure QR-Based File Sharing Platform

[![Live Demo](https://img.shields.io/badge/LIVE-DEMO-00E5FF?style=for-the-badge&logo=vercel&logoColor=white)](https://qrvault.onrender.com/)
[![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-00C853?style=for-the-badge)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-44%20Passed-00C853?style=for-the-badge&logo=pytest&logoColor=white)](#testing)

**Encrypt. Share. Scan. Download.**

A cybersecurity internship project implementing end-to-end encrypted file sharing
with QR codes, expiring links, and access controls.

[🚀 Try Live Demo](https://qrvault.onrender.com/) · [📖 Documentation](#installation) · [🔒 Security](#security-features)

---

![QRVault Demo](https://img.shields.io/badge/QRVault-Workflow-0B1F3A?style=flat-square&labelColor=0B1F3A&color=00E5FF)

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  UPLOAD  │───▶│ ENCRYPT  │───▶│ QR CODE  │───▶│ DOWNLOAD │
│  File    │    │ AES-256  │    │ Generate │    │ Decrypt  │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

</div>


---

## 🔍 Overview

QRVault is a **production-style cybersecurity project** that enables secure file sharing through encrypted uploads, QR code generation, and token-based access control. Files are encrypted **client-side** using AES-256-GCM before upload, and decryption happens **locally** in the receiver's browser. The server **never** has access to plaintext files or encryption keys.

> **Note:** This is a real working application, not a static UI prototype.

---

## 🎯 Project Objective

> *"Build a secure P2P or cloud-based file sharing platform with end-to-end encryption, expiring links, and access controls."*

QRVault satisfies this objective through a secure QR-based file-sharing workflow with:
- Client-side AES-256-GCM encryption
- Server-enforced expiring links
- Configurable download limits
- Instant access revocation
- No account required

---

## 🌐 Live Demo

**🔗 [https://qrvault.onrender.com](https://qrvault.onrender.com/)**

### Try It Now:
1. Go to [qrvault.onrender.com](https://qrvault.onrender.com/)
2. Click **"Secure File Share"**
3. Select any file
4. Set expiry time and download limit
5. Click **"Encrypt & Generate Secure Share"**
6. Copy the link or scan the QR code
7. Open the link in another browser/device
8. Click **"Download Securely"**
9. Your file is decrypted automatically!

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🔐 **AES-256-GCM Encryption** | Files encrypted in browser before upload using Web Crypto API |
| 📱 **QR Code Sharing** | Generate QR codes containing secure share URLs |
| ⏱️ **Expiring Links** | Server-enforced expiration (5 min to 24 hours) |
| 📊 **Download Limits** | Configurable maximum download count (1-50) |
| 🚫 **Instant Revocation** | Revoke access to shared files at any time |
| 🔑 **Token-Based Access** | No accounts needed, cryptographically secure tokens |
| 🗑️ **Auto-Delete** | Files auto-deleted on expiry, limit hit, or revocation |
| 🔍 **Audit Logging** | All access attempts logged for security monitoring |
| 🛡️ **Security Headers** | CSP, X-Frame-Options, nosniff, and more |
| ⚡ **Rate Limiting** | Protection against brute-force and abuse |
| 📱 **Mobile Friendly** | Works on Android, iPhone, and desktop browsers |
| 🔄 **No Registration** | Share files without creating an account |

---

## 🏗 Architecture

```
QRVault/
├── app.py                        # Flask application factory
├── config.py                     # Configuration management
├── requirements.txt              # Python dependencies
├── render.yaml                   # Render deployment config
├── Procfile                      # Process file for deployment
│
├── database/
│   ├── db.py                     # SQLite database setup
│   └── models.py                 # Share, AuditLog models
│
├── routes/
│   ├── main.py                   # Landing page routes
│   ├── upload.py                 # File upload + encryption API
│   ├── sharing.py                # Share/manage page routes
│   └── api.py                    # Download, revoke, status APIs
│
├── security/
│   ├── tokens.py                 # 256-bit token generation
│   ├── validation.py             # Input & file validation
│   ├── rate_limit.py             # IP-based rate limiting
│   └── headers.py                # Security headers (CSP, etc.)
│
├── services/
│   ├── file_service.py           # Encrypted file storage ops
│   ├── cleanup_service.py        # Expired file cleanup
│   └── qr_service.py             # QR code generation
│
├── static/
│   ├── css/style.css             # Cybersecurity-themed UI
│   └── js/
│       ├── encryption.js         # Web Crypto API module
│       ├── upload.js             # Upload workflow
│       ├── share.js              # Download workflow
│       └── qrcode.min.js         # QR code library
│
├── templates/                    # Jinja2 HTML templates
│   ├── base.html
│   ├── index.html                # Landing page
│   ├── upload.html               # File upload page
│   ├── share.html                # Download page
│   ├── manage.html               # Management panel
│   └── error.html                # Error states
│
├── storage/encrypted/            # Encrypted file storage
└── tests/                        # Pytest test suite
    ├── test_upload.py
    ├── test_access.py
    ├── test_expiry.py
    ├── test_download_limit.py
    └── test_security.py
```

---

## 🔒 Encryption Design

### Why AES-256-GCM?

| Property | Benefit |
|----------|---------|
| **Authenticated Encryption** | Provides confidentiality AND integrity |
| **Hardware Accelerated** | Fast on modern CPUs (AES-NI) |
| **Industry Standard** | Widely supported and well-analyzed |
| **Bulk Encryption** | Efficient for large files (vs RSA) |

---
## 🛠 Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Backend** | Python 3.x, Flask | Web server, API, file handling |
| **Frontend** | HTML5, CSS3, Vanilla JS | UI, client-side encryption |
| **Database** | SQLite | Share metadata, audit logs |
| **Encryption** | Web Crypto API (AES-256-GCM) | Client-side file encryption |
| **QR Code** | qrcode.js (client-side) | QR code generation |
| **Security** | secrets, hashlib, Werkzeug | Token generation, hashing |
| **Deployment** | Render | Cloud hosting |
| **Testing** | pytest | Automated test suite |

---

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/Jyotibala-cyber/QRVault.git
cd QRVault

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Initialize database
python -c "from database.db import init_db; init_db()"

# 6. Run the application
python app.py
```

### Environment Variables

```bash
# Copy .env.example to .env
cp .env.example .env

# Edit .env with your settings
SECRET_KEY=your-super-secret-key-here
DATABASE_URL=instance/qrvault.db
STORAGE_PATH=storage/encrypted
MAX_FILE_SIZE=52428800
```
---

## 🚀 Running Locally

```bash
# Development mode
python app.py

# Production mode (with gunicorn)
gunicorn app:app --bind 0.0.0.0:5000
```

The application will be available at: **http://localhost:5000**

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_upload.py -v

# Run with coverage
pytest tests/ -v --tb=short

# Run specific test
pytest tests/test_access.py::TestAccessControl::test_valid_token_access -v
```

---

## 🛡 Security Features

### Implemented Security Measures

| # | Feature | Status |
|---|---------|--------|
| 1 | Cryptographically secure random tokens (256-bit) | ✅ |
| 2 | AES-256-GCM encryption | ✅ |
| 3 | Client-side encryption (browser) | ✅ |
| 4 | Client-side decryption (browser) | ✅ |
| 5 | Expiring links (server-enforced) | ✅ |
| 6 | Download limits (server-enforced) | ✅ |
| 7 | Instant revocation | ✅ |
| 8 | Filename sanitization | ✅ |
| 9 | File size limits | ✅ |
| 10 | Input validation | ✅ |
| 11 | Secure server-side filenames | ✅ |
| 12 | Rate limiting (IP-based) | ✅ |
| 13 | Security headers (CSP, X-Frame, etc.) | ✅ |
| 14 | Safe error messages | ✅ |
| 15 | No plaintext file storage | ✅ |
| 16 | No encryption key logging | ✅ |
| 17 | No arbitrary file access | ✅ |
| 18 | Path traversal protection | ✅ |
| 19 | Auto-delete on expiry/limit/revoke | ✅ |
| 20 | Audit logging | ✅ |


## 🚀 Deployment

### Render (Current)

The live deployment is on [Render](https://qrvault.onrender.com/):

---

## ⚠️ Limitations

| Limitation | Impact | Mitigation |
|-----------|--------|------------|
| Render free tier | Files lost on restart | Auto-delete handles this |
| In-memory rate limiting | Resets on server restart | Acceptable for demo |
| Single-server deployment | Not distributed | Documented limitation |
| Client-side encryption trust | Relies on browser Web Crypto API | Standard practice |
| SQLite | Not for high concurrency | Sufficient for demo |
| No HTTPS on localhost | Fragment visible in dev only | Production uses HTTPS |
| Ephemeral filesystem (Render) | Files not permanent | Auto-delete feature |

---

## 🔮 Future Enhancements

- [ ] End-to-end RSA key exchange demo
- [ ] File chunking for large files
- [ ] Persistent rate limiting (Redis)
- [ ] User accounts for file management dashboard
- [ ] Multi-file sharing (zip)
- [ ] File preview before download
- [ ] Webhook notifications on download
- [ ] API key authentication
- [ ] Docker containerization
- [ ] Kubernetes orchestration
- [ ] S3/R2 cloud storage integration
- [ ] File integrity verification (SHA-256 checksum)

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## ⚠️ Disclaimer

> **QRVault is an educational cybersecurity project developed for internship requirements.**
>
> Use it only for files and systems you are authorized to manage. The developers assume no responsibility for misuse of this software.
>
> **Do NOT use for:**
> - Sharing sensitive/confidential data in production
> - Storing critical files without backup
> - Any unauthorized file sharing activity

---

<div align="center">

**Built with ❤️ for Cybersecurity Internship**

[⬆ Back to Top](#-qrvault)

</div>
