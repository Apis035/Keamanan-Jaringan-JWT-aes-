const fileListEl = document.getElementById("fileList");
const emptyStateEl = document.getElementById("emptyState");
const messageEl = document.getElementById("message");
const fileInput = document.getElementById("fileInput");
const dropZone = document.getElementById("dropZone");
const progressWrap = document.getElementById("progressWrap");
const progressBar = document.getElementById("progressBar");
const progressText = document.getElementById("progressText");
const fileCountEl = document.getElementById("fileCount");
const totalSizeEl = document.getElementById("totalSize");

if (!getToken()) {
    window.location.href = "login.html";
}

function showMessage(text, type) {
    setMessage(messageEl, text, type);
    if (text) {
        clearTimeout(showMessage.timer);
        showMessage.timer = setTimeout(() => setMessage(messageEl, "", ""), 5000);
    }
}

function makeButton(label, className, onClick) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = className;
    btn.textContent = label;
    btn.addEventListener("click", onClick);
    return btn;
}

function renderFiles(files) {
    fileListEl.replaceChildren();

    fileCountEl.textContent = files.length;
    totalSizeEl.textContent = formatSize(
        files.reduce((sum, f) => sum + f.file_size, 0)
    );

    emptyStateEl.style.display = files.length ? "none" : "block";

    files.forEach((file) => {
        const tr = document.createElement("tr");

        const nameTd = document.createElement("td");
        nameTd.className = "file-name";
        nameTd.textContent = file.original_name; // textContent: aman dari XSS

        const sizeTd = document.createElement("td");
        sizeTd.textContent = formatSize(file.file_size);

        const dateTd = document.createElement("td");
        dateTd.textContent = formatDate(file.created_at);

        const actionTd = document.createElement("td");
        actionTd.className = "actions";

        const dlBtn = makeButton("Unduh", "btn btn-small", async () => {
            dlBtn.disabled = true;
            dlBtn.textContent = "Mendekripsi...";
            try {
                await downloadFile(file.id, file.original_name);
            } catch (e) {
                showMessage(e.message, "error");
            } finally {
                dlBtn.disabled = false;
                dlBtn.textContent = "Unduh";
            }
        });

        const delBtn = makeButton("Hapus", "btn btn-small btn-danger", async () => {
            if (!confirm(`Hapus "${file.original_name}" secara permanen?`)) return;
            delBtn.disabled = true;
            try {
                await deleteFile(file.id);
                showMessage("File berhasil dihapus.", "success");
                await refreshFiles();
            } catch (e) {
                showMessage(e.message, "error");
                delBtn.disabled = false;
            }
        });

        actionTd.append(dlBtn, delBtn);
        tr.append(nameTd, sizeTd, dateTd, actionTd);
        fileListEl.appendChild(tr);
    });
}

async function refreshFiles() {
    try {
        renderFiles(await fetchFiles());
    } catch (e) {
        showMessage(e.message, "error");
    }
}

async function handleUpload(file) {
    if (!file) return;

    if (file.size === 0) {
        showMessage("File kosong tidak dapat diunggah.", "error");
        return;
    }

    if (file.size > MAX_UPLOAD_SIZE) {
        showMessage("Ukuran file melebihi batas 100 MB.", "error");
        return;
    }

    progressWrap.style.display = "block";
    progressBar.style.width = "0%";
    progressText.textContent = `Mengunggah ${file.name}... 0%`;

    try {
        await uploadFile(file, (percent) => {
            progressBar.style.width = `${percent}%`;
            progressText.textContent =
                percent < 100
                    ? `Mengunggah ${file.name}... ${percent}%`
                    : "Mengenkripsi di server...";
        });

        showMessage("File berhasil dienkripsi dan diunggah.", "success");
        await refreshFiles();
    } catch (e) {
        showMessage(e.message, "error");
    } finally {
        progressWrap.style.display = "none";
        fileInput.value = "";
    }
}

fileInput.addEventListener("change", () => handleUpload(fileInput.files[0]));

["dragenter", "dragover"].forEach((evt) =>
    dropZone.addEventListener(evt, (e) => {
        e.preventDefault();
        dropZone.classList.add("dragover");
    })
);

["dragleave", "drop"].forEach((evt) =>
    dropZone.addEventListener(evt, (e) => {
        e.preventDefault();
        dropZone.classList.remove("dragover");
    })
);

dropZone.addEventListener("drop", (e) => handleUpload(e.dataTransfer.files[0]));

document.getElementById("logoutButton").addEventListener("click", logout);

async function init() {
    try {
        const me = await authRequest(API_ENDPOINTS.me);
        document.getElementById("userName").textContent = me.data.name;
        document.getElementById("userEmail").textContent = me.data.email;
    } catch (e) {
        showMessage(e.message, "error");
    }
    await refreshFiles();
}

init();
