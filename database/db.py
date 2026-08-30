import sqlite3
import os
from pathlib import Path

DB_PATH = os.environ.get(
    "DATABASE_URL", str(Path(__file__).resolve().parent.parent / "instance" / "qrvault.db")
)


def get_db():
    """Get database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Initialize database tables."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS shares (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token_hash TEXT UNIQUE NOT NULL,
            management_token_hash TEXT UNIQUE NOT NULL,
            original_filename TEXT NOT NULL,
            stored_filename TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            mime_type TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            max_downloads INTEGER NOT NULL DEFAULT 3,
            download_count INTEGER NOT NULL DEFAULT 0,
            revoked INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'active',
            password_hash TEXT,
            created_ip TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_shares_token_hash ON shares(token_hash);
        CREATE INDEX IF NOT EXISTS idx_shares_management_token ON shares(management_token_hash);
        CREATE INDEX IF NOT EXISTS idx_shares_status ON shares(status);
        CREATE INDEX IF NOT EXISTS idx_shares_expires_at ON shares(expires_at);

        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            share_id INTEGER,
            action TEXT NOT NULL,
            details TEXT,
            ip_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (share_id) REFERENCES shares(id) ON DELETE SET NULL
        );
    """)
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
