/**
 * QRVault Upload Module
 * Handles file selection, encryption, upload, and share generation
 */
(function () {
    const dropZone = document.getElementById("dropZone");
    const fileInput = document.getElementById("fileInput");
    const fileInfo = document.getElementById("fileInfo");
    const fileName = document.getElementById("fileName");
    const fileSize = document.getElementById("fileSize");
    const fileType = document.getElementById("fileType");
    const encryptionStatus = document.getElementById("encryptionStatus");
    const encryptBtn = document.getElementById("encryptBtn");
    const step1 = document.getElementById("upload-step-1");
    const step2 = document.getElementById("upload-step-2");
    const step3 = document.getElementById("upload-step-3");
    const progressText = document.getElementById("encryptionProgress");

    let selectedFile = null;

    function formatSize(bytes) {
        if (bytes === 0) return "0 B";
        const units = ["B", "KB", "MB", "GB"];
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return (bytes / Math.pow(1024, i)).toFixed(i > 0 ? 1 : 0) + " " + units[i];
    }

    function showFile(file) {
        selectedFile = file;
        fileName.textContent = file.name;
        fileSize.textContent = formatSize(file.size);
        fileType.textContent = file.type || "Unknown";
        encryptionStatus.textContent = "⏳ Pending";
        encryptionStatus.className = "value";
        fileInfo.classList.remove("hidden");
        dropZone.style.display = "none";
        encryptBtn.disabled = false;
    }

    dropZone.addEventListener("click", () => fileInput.click());

    dropZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropZone.classList.add("drag-over");
    });

    dropZone.addEventListener("dragleave", () => {
        dropZone.classList.remove("drag-over");
    });

    dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropZone.classList.remove("drag-over");
        if (e.dataTransfer.files.length) showFile(e.dataTransfer.files[0]);
    });

    fileInput.addEventListener("change", () => {
        if (fileInput.files.length) showFile(fileInput.files[0]);
    });

    encryptBtn.addEventListener("click", async () => {
        if (!selectedFile) return;

        step1.classList.add("hidden");
        step2.classList.remove("hidden");

        try {
            progressText.textContent = "Reading file...";
            const arrayBuffer = await selectedFile.arrayBuffer();

            progressText.textContent = "Generating encryption key...";
            await new Promise(r => setTimeout(r, 300));

            progressText.textContent = "Encrypting with AES-256-GCM...";
            const { encryptedData, keyBase64 } = await QRVaultCrypto.encryptFile(arrayBuffer);

            encryptionStatus.textContent = "✓ Encrypted locally";
            encryptionStatus.className = "value status-success";

            const expiry = document.getElementById("expirySelect").value;
            const maxDownloads = document.getElementById("downloadsSelect").value;
            const passwordInput = document.getElementById("passwordInput");
            let passwordHash = "";
            if (passwordInput && passwordInput.value) {
                passwordHash = await QRVaultCrypto.hashPassword(passwordInput.value);
            }

            progressText.textContent = "Uploading encrypted file...";
            const formData = new FormData();
            const blob = new Blob([encryptedData], { type: "application/octet-stream" });
            formData.append("encrypted_file", blob, selectedFile.name + ".enc");
            formData.append("expiry", expiry);
            formData.append("max_downloads", maxDownloads);
            if (passwordHash) formData.append("password_hash", passwordHash);

            const response = await fetch("/api/upload", {
                method: "POST",
                body: formData,
            });

            const result = await response.json();
            if (!response.ok) throw new Error(result.error || "Upload failed");

            const shareUrl = result.share_url + "#" + keyBase64;

            document.getElementById("shareLink").value = shareUrl;
            document.getElementById("qrCode").src = result.qr_code;
            document.getElementById("shareStatus").textContent = "ACTIVE";
            document.getElementById("shareDownloads").textContent = "0 / " + result.max_downloads;

            const expiresAt = new Date(result.expires_at);
            function updateCountdown() {
                const now = new Date();
                const diff = Math.max(0, Math.floor((expiresAt - now) / 1000));
                const m = Math.floor(diff / 60);
                const s = diff % 60;
                document.getElementById("shareExpiry").textContent =
                    String(m).padStart(2, "0") + ":" + String(s).padStart(2, "0");
                if (diff > 0) setTimeout(updateCountdown, 1000);
                else document.getElementById("shareStatus").textContent = "EXPIRED";
            }
            updateCountdown();

            document.getElementById("manageLink").href = "/manage/" + result.management_token;

            document.getElementById("downloadQrBtn").addEventListener("click", () => {
                const link = document.createElement("a");
                link.href = result.qr_code;
                link.download = "qrvault-" + result.share_token.slice(0, 8) + ".png";
                link.click();
            });

            document.getElementById("copyLinkBtn").addEventListener("click", () => {
                navigator.clipboard.writeText(shareUrl).then(() => {
                    document.getElementById("copyLinkBtn").textContent = "Copied!";
                    setTimeout(() => document.getElementById("copyLinkBtn").textContent = "Copy", 2000);
                });
            });

            document.getElementById("newShareBtn").addEventListener("click", () => {
                window.location.reload();
            });

            step2.classList.add("hidden");
            step3.classList.remove("hidden");

        } catch (err) {
            progressText.textContent = "Error: " + err.message;
            setTimeout(() => {
                step2.classList.add("hidden");
                step1.classList.remove("hidden");
            }, 3000);
        }
    });
})();
