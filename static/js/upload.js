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
    let currentKeyBase64 = null;

    function formatSize(bytes) {
        if (bytes === 0) return "0 B";
        const units = ["B", "KB", "MB", "GB"];
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return (bytes / Math.pow(1024, i)).toFixed(i > 0 ? 1 : 0) + " " + units[i];
    }

    function showFile(file) {
        selectedFile = file;
        currentKeyBase64 = null;
        fileName.textContent = file.name;
        fileSize.textContent = formatSize(file.size);
        fileType.textContent = file.type || "Unknown";
        encryptionStatus.textContent = "\u23F3 Pending";
        encryptionStatus.className = "value";
        fileInfo.classList.remove("hidden");
        dropZone.style.display = "none";
        encryptBtn.disabled = false;
        encryptBtn.textContent = "Encrypt & Generate Secure Share";
    }

    function showError(msg) {
        progressText.textContent = "Error: " + msg;
        setTimeout(function () {
            step2.classList.add("hidden");
            step1.classList.remove("hidden");
            encryptBtn.disabled = false;
            encryptBtn.textContent = "Encrypt & Generate Secure Share";
        }, 3000);
    }

    function encryptFile(file) {
        return new Promise(function (resolve, reject) {
            var reader = new FileReader();
            reader.onload = function () {
                var arrayBuffer = reader.result;
                QRVaultCrypto.encryptFile(arrayBuffer)
                    .then(resolve)
                    .catch(reject);
            };
            reader.onerror = function () {
                reject(new Error("Failed to read file"));
            };
            reader.readAsArrayBuffer(file);
        });
    }

    function doUpload() {
        if (!selectedFile) return;

        step1.classList.add("hidden");
        step2.classList.remove("hidden");
        encryptBtn.disabled = true;

        progressText.textContent = "Reading file...";

        setTimeout(function () {
            progressText.textContent = "Encrypting with AES-256-GCM...";

            encryptFile(selectedFile).then(function (result) {
                var encryptedData = result.encryptedData;
                currentKeyBase64 = result.keyBase64;

                encryptionStatus.textContent = "\u2713 Encrypted locally";
                encryptionStatus.className = "value status-success";

                var expiry = document.getElementById("expirySelect").value;
                var maxDownloads = document.getElementById("downloadsSelect").value;
                var passwordInput = document.getElementById("passwordInput");
                var passwordHash = "";

                function hashPw(pw) {
                    return QRVaultCrypto.hashPassword(pw);
                }

                var pwPromise = (passwordInput && passwordInput.value)
                    ? hashPw(passwordInput.value)
                    : Promise.resolve("");

                pwPromise.then(function (ph) {
                    passwordHash = ph;
                    progressText.textContent = "Uploading encrypted file...";

                    var formData = new FormData();
                    var blob = new Blob([encryptedData], { type: "application/octet-stream" });
                    formData.append("encrypted_file", blob, selectedFile.name + ".enc");
                    formData.append("expiry", expiry);
                    formData.append("max_downloads", maxDownloads);
                    if (passwordHash) formData.append("password_hash", passwordHash);

                    return fetch("/api/upload", {
                        method: "POST",
                        body: formData,
                    });
                }).then(function (response) {
                    return response.json().then(function (data) {
                        if (!response.ok) throw new Error(data.error || "Upload failed");
                        return data;
                    });
                }).then(function (result) {
                    var shareUrl = result.share_url + "#" + currentKeyBase64;

                    document.getElementById("shareLink").value = shareUrl;
                    document.getElementById("shareStatus").textContent = "ACTIVE";
                    document.getElementById("shareDownloads").textContent = "0 / " + result.max_downloads;

                    // Generate QR code CLIENT-SIDE with full URL (including key fragment)
                    var qrContainer = document.getElementById("qrCode");
                    qrContainer.innerHTML = "";
                    if (typeof QRCode !== "undefined") {
                        new QRCode(qrContainer, {
                            text: shareUrl,
                            width: 250,
                            height: 250,
                            colorDark: "#0B1F3A",
                            colorLight: "#ffffff",
                        });
                    } else {
                        qrContainer.innerHTML = '<p style="color:#FF5252;">QR library not loaded. Copy the link instead.</p>';
                    }

                    var expiresAt = new Date(result.expires_at);
                    function updateCountdown() {
                        var now = new Date();
                        var diff = Math.max(0, Math.floor((expiresAt - now) / 1000));
                        var m = Math.floor(diff / 60);
                        var s = diff % 60;
                        document.getElementById("shareExpiry").textContent =
                            String(m).padStart(2, "0") + ":" + String(s).padStart(2, "0");
                        if (diff > 0) setTimeout(updateCountdown, 1000);
                        else document.getElementById("shareStatus").textContent = "EXPIRED";
                    }
                    updateCountdown();

                    document.getElementById("manageLink").href = "/manage/" + result.management_token;

                    document.getElementById("downloadQrBtn").onclick = function () {
                        var qrImg = qrContainer.querySelector("img");
                        if (qrImg) {
                            var link = document.createElement("a");
                            link.href = qrImg.src;
                            link.download = "qrvault-" + result.share_token.slice(0, 8) + ".png";
                            link.click();
                        }
                    };

                    document.getElementById("copyLinkBtn").onclick = function () {
                        navigator.clipboard.writeText(shareUrl).then(function () {
                            document.getElementById("copyLinkBtn").textContent = "Copied!";
                            setTimeout(function () {
                                document.getElementById("copyLinkBtn").textContent = "Copy";
                            }, 2000);
                        }).catch(function () {
                            var inp = document.getElementById("shareLink");
                            inp.select();
                            document.execCommand("copy");
                            document.getElementById("copyLinkBtn").textContent = "Copied!";
                            setTimeout(function () {
                                document.getElementById("copyLinkBtn").textContent = "Copy";
                            }, 2000);
                        });
                    };

                    document.getElementById("newShareBtn").onclick = function () {
                        window.location.reload();
                    };

                    step2.classList.add("hidden");
                    step3.classList.remove("hidden");

                }).catch(function (err) {
                    showError(err.message);
                });
            }).catch(function (err) {
                showError(err.message);
            });
        }, 100);
    }

    dropZone.addEventListener("click", function () { fileInput.click(); });

    dropZone.addEventListener("dragover", function (e) {
        e.preventDefault();
        dropZone.classList.add("drag-over");
    });

    dropZone.addEventListener("dragleave", function () {
        dropZone.classList.remove("drag-over");
    });

    dropZone.addEventListener("drop", function (e) {
        e.preventDefault();
        dropZone.classList.remove("drag-over");
        if (e.dataTransfer.files.length) showFile(e.dataTransfer.files[0]);
    });

    fileInput.addEventListener("change", function () {
        if (fileInput.files.length) showFile(fileInput.files[0]);
    });

    encryptBtn.addEventListener("click", function () {
        doUpload();
    });
})();
