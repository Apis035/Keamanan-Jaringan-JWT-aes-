async function apiRequest(url, options = {}) {
    const response = await fetch(url, options);

    const contentType = response.headers.get("content-type");

    if (!response.ok) {
        let errorData = {};

        if (contentType && contentType.includes("application/json")) {
            errorData = await response.json();
        }

        const error = new Error(
            errorData.message || errorData.msg || "Terjadi kesalahan pada server."
        );
        error.status = response.status;
        throw error;
    }

    if (contentType && contentType.includes("application/json")) {
        return await response.json();
    }

    return response;
}

function getToken() {
    return localStorage.getItem("access_token");
}

function logout() {
    localStorage.removeItem("access_token");
    window.location.href = "login.html";
}

// Request dengan header Authorization. Jika token kedaluwarsa/tidak valid
// (401 atau 422 dari flask-jwt-extended), pengguna otomatis di-logout.
async function authRequest(url, options = {}) {
    const token = getToken();

    if (!token) {
        logout();
        throw new Error("Sesi berakhir. Silakan login kembali.");
    }

    options.headers = {
        ...(options.headers || {}),
        Authorization: `Bearer ${token}`
    };

    try {
        return await apiRequest(url, options);
    } catch (error) {
        if (error.status === 401 || error.status === 422) {
            logout();
        }
        throw error;
    }
}
