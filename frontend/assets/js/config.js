const API_BASE_URL = "http://127.0.0.1:5000/api";

const API_ENDPOINTS = {
    register: `${API_BASE_URL}/auth/register`,
    login: `${API_BASE_URL}/auth/login`,
    me: `${API_BASE_URL}/auth/me`,

    files: `${API_BASE_URL}/files`,
    upload: `${API_BASE_URL}/files/upload`,
    download: (id) => `${API_BASE_URL}/files/${id}/download`,
    remove: (id) => `${API_BASE_URL}/files/${id}`
};

// Harus sama dengan MAX_CONTENT_LENGTH di backend (100 MB)
const MAX_UPLOAD_SIZE = 100 * 1024 * 1024;
