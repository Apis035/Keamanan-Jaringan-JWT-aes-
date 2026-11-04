// Operasi file ke backend (tanpa menyentuh DOM)

async function fetchFiles() {
    const result = await authRequest(API_ENDPOINTS.files);
    return result.data || [];
}

// Upload memakai XMLHttpRequest agar progress bisa ditampilkan
function uploadFile(file, onProgress) {
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        const formData = new FormData();
        formData.append("file", file);

        xhr.open("POST", API_ENDPOINTS.upload);
        xhr.setRequestHeader("Authorization", `Bearer ${getToken()}`);

        xhr.upload.onprogress = (e) => {
            if (e.lengthComputable && onProgress) {
                onProgress(Math.round((e.loaded / e.total) * 100));
            }
        };

        xhr.onload = () => {
            let body = {};
            try { body = JSON.parse(xhr.responseText); } catch (_) {}

            if (xhr.status >= 200 && xhr.status < 300) {
                resolve(body);
            } else if (xhr.status === 401 || xhr.status === 422) {
                logout();
                reject(new Error("Sesi berakhir. Silakan login kembali."));
            } else {
                reject(new Error(body.message || body.msg || "Upload gagal."));
            }
        };

        xhr.onerror = () => reject(new Error("Tidak dapat terhubung ke server."));
        xhr.send(formData);
    });
}

// Download: ambil sebagai blob (header Authorization tidak bisa dipakai di <a href>)
async function downloadFile(id, originalName) {
    const response = await authRequest(API_ENDPOINTS.download(id));
    const blob = await response.blob();

    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = originalName;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
}

async function deleteFile(id) {
    return authRequest(API_ENDPOINTS.remove(id), { method: "DELETE" });
}

function formatSize(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
    return `${(bytes / 1024 / 1024 / 1024).toFixed(2)} GB`;
}

function formatDate(iso) {
    return new Date(iso).toLocaleString("id-ID", {
        day: "2-digit", month: "short", year: "numeric",
        hour: "2-digit", minute: "2-digit"
    });
}
