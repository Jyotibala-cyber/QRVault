/**
 * QRVault Client-Side Encryption Module
 * AES-256-GCM encryption and decryption using Web Crypto API
 */
const QRVaultCrypto = {
    /**
     * Generate a random AES-256-GCM key
     */
    async generateKey() {
        return await window.crypto.subtle.generateKey(
            { name: "AES-GCM", length: 256 },
            true,
            ["encrypt", "decrypt"]
        );
    },

    /**
     * Generate a random initialization vector (IV)
     */
    generateIV() {
        return window.crypto.getRandomValues(new Uint8Array(12));
    },

    /**
     * Export key to raw format for URL storage
     */
    async exportKey(key) {
        const raw = await window.crypto.subtle.exportKey("raw", key);
        return this.arrayBufferToBase64(raw);
    },

    /**
     * Import key from raw format
     */
    async importKey(base64Key) {
        const raw = this.base64ToArrayBuffer(base64Key);
        return await window.crypto.subtle.importKey(
            "raw",
            raw,
            { name: "AES-GCM", length: 256 },
            false,
            ["decrypt"]
        );
    },

    /**
     * Encrypt file data using AES-256-GCM
     * Returns: { encryptedData, iv, keyBase64 }
     */
    async encryptFile(fileData) {
        const key = await this.generateKey();
        const iv = this.generateIV();

        const encrypted = await window.crypto.subtle.encrypt(
            { name: "AES-GCM", iv: iv },
            key,
            fileData
        );

        const keyBase64 = await this.exportKey(key);
        const ivBase64 = this.arrayBufferToBase64(iv.buffer);

        // Prepend IV to encrypted data for storage
        const encryptedArray = new Uint8Array(encrypted);
        const result = new Uint8Array(iv.length + encryptedArray.length);
        result.set(iv, 0);
        result.set(encryptedArray, iv.length);

        return {
            encryptedData: result.buffer,
            keyBase64: keyBase64,
            ivBase64: ivBase64,
        };
    },

    /**
     * Decrypt file data using AES-256-GCM
     */
    async decryptFile(encryptedDataWithIV, keyBase64) {
        const data = new Uint8Array(encryptedDataWithIV);
        const iv = data.slice(0, 12);
        const ciphertext = data.slice(12);

        const key = await this.importKey(keyBase64);

        const decrypted = await window.crypto.subtle.decrypt(
            { name: "AES-GCM", iv: iv },
            key,
            ciphertext
        );

        return decrypted;
    },

    /**
     * Compute SHA-256 hash of data
     */
    async hashData(data) {
        const hashBuffer = await window.crypto.subtle.digest("SHA-256", data);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    },

    /**
     * Convert ArrayBuffer to Base64 string
     */
    arrayBufferToBase64(buffer) {
        const bytes = new Uint8Array(buffer);
        let binary = '';
        for (let i = 0; i < bytes.length; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return window.btoa(binary);
    },

    /**
     * Convert Base64 string to ArrayBuffer
     */
    base64ToArrayBuffer(base64) {
        const binary = window.atob(base64);
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) {
            bytes[i] = binary.charCodeAt(i);
        }
        return bytes.buffer;
    },

    /**
     * Hash password with SHA-256 (for optional password protection)
     */
    async hashPassword(password) {
        const encoder = new TextEncoder();
        const data = encoder.encode(password);
        return await this.hashData(data);
    }
};
