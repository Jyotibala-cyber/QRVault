/**
 * QRVault Share/Download Module
 * Handles secure file download and client-side decryption
 */
(function () {
    const token = window.__SHARE_TOKEN__;
    let remaining = window.__REMAINING__;
    const hasPassword = window.__HAS_PASSWORD__;

    const countdownEl = document.getElementById("shareCountdown");
    const downloadBtn = document.getElementById("downloadBtn");
    const modal = document.getElementById("downloadModal");
    const cancelBtn = document.getElementById("cancelDownload");
    const acceptBtn = document.getElementById("acceptDownload");

    function updateCountdown() {
        if (remaining <= 0) {
            countdownEl.textContent = "Expired";
            countdownEl.style.color = "#FF5252";
            downloadBtn.disabled = true;
            downloadBtn.textContent = "Link Expired";
            const badge = document.getElementById("shareStatusBadge");
            if (badge) {
                badge.textContent = "EXPIRED";
                badge.className = "detail-value status-badge status-expired";
            }
            return;
        }
        const h = Math.floor(remaining / 3600);
        const m = Math.floor((remaining % 3600) / 60);
        const s = remaining % 60;
        countdownEl.textContent =
            (h > 0 ? h + ":" : "") +
            String(m).padStart(2, "0") + ":" +
            String(s).padStart(2, "0");
        remaining--;
        setTimeout(updateCountdown, 1000);
    }

    updateCountdown();

    // Poll status every 30 seconds
    setInterval(async () => {
        try {
            const resp = await fetch("/api/share/" + token + "/status");
            const data = await resp.json();
            if (data.status !== "active") {
                downloadBtn.disabled = true;
                if (data.status === "expired") downloadBtn.textContent = "Link Expired";
                else if (data.status === "revoked") downloadBtn.textContent = "Access Revoked";
                else if (data.status === "limit_reached") downloadBtn.textContent = "Download Limit Reached";
                const badge = document.getElementById("shareStatusBadge");
                if (badge) {
                    badge.textContent = data.status.toUpperCase();
                    badge.className = "detail-value status-badge status-" + data.status;
                }
            }
            document.getElementById("shareDownloadCount").textContent =
                data.download_count + " / " + data.max_downloads;
        } catch (e) { /* ignore polling errors */ }
    }, 30000);

    downloadBtn.addEventListener("click", () => {
        modal.classList.remove("hidden");
    });

    cancelBtn.addEventListener("click", () => {
        modal.classList.add("hidden");
    });

    document.querySelector(".modal-backdrop").addEventListener("click", () => {
        modal.classList.add("hidden");
    });

    acceptBtn.addEventListener("click", async () => {
        acceptBtn.disabled = true;
        acceptBtn.textContent = "Preparing...";

        try {
            const body = {};
            if (hasPassword) {
                const pwInput = document.getElementById("passwordInput");
                if (!pwInput || !pwInput.value) {
                    const errEl = document.getElementById("passwordError");
                    if (errEl) errEl.style.display = "block";
                    acceptBtn.disabled = false;
                    acceptBtn.textContent = "Accept & Download";
                    return;
                }
                body.password = pwInput.value;
            }

            const authResp = await fetch("/api/share/" + token + "/authorize", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body),
            });

            const authData = await authResp.json();
            if (!authResp.ok) {
                if (authData.password_required) {
                    const errEl = document.getElementById("passwordError");
                    if (errEl) errEl.style.display = "block";
                } else {
                    alert(authData.error || "Authorization failed");
                }
                acceptBtn.disabled = false;
                acceptBtn.textContent = "Accept & Download";
                return;
            }

            acceptBtn.textContent = "Downloading...";

            const dlResp = await fetch("/api/share/" + token + "/download");
            if (!dlResp.ok) {
                const errData = await dlResp.json();
                throw new Error(errData.error || "Download failed");
            }

            const encryptedBlob = await dlResp.blob();
            const encryptedArrayBuffer = await encryptedBlob.arrayBuffer();

            acceptBtn.textContent = "Decrypting...";

            const urlHash = window.location.hash.substring(1);
            if (!urlHash) {
                throw new Error("Decryption key not found in URL. Make sure you are using the complete share link.");
            }

            const decryptedBuffer = await QRVaultCrypto.decryptFile(encryptedArrayBuffer, urlHash);

            const originalName = authData.filename || "downloaded_file";
            const mimeType = authData.mime_type || "application/octet-stream";
            const decryptedBlob = new Blob([decryptedBuffer], { type: mimeType });

            var url = URL.createObjectURL(decryptedBlob);
            var a = document.createElement("a");
            a.href = url;
            a.download = originalName;
            a.style.display = "none";
            document.body.appendChild(a);

            requestAnimationFrame(function () {
                a.click();
                setTimeout(function () {
                    URL.revokeObjectURL(url);
                    if (a.parentNode) a.parentNode.removeChild(a);
                }, 500);
            });

            modal.classList.add("hidden");

            downloadBtn.textContent = "Downloaded Successfully";
            downloadBtn.disabled = true;
            downloadBtn.style.background = "#00C853";

            const countEl = document.getElementById("shareDownloadCount");
            if (countEl) {
                const parts = countEl.textContent.split("/");
                const newCount = parseInt(parts[0].trim()) + 1;
                countEl.textContent = newCount + " /" + parts[1];
            }

        } catch (err) {
            alert("Download/decryption error: " + err.message);
            acceptBtn.disabled = false;
            acceptBtn.textContent = "Accept & Download";
        }
    });
})();
