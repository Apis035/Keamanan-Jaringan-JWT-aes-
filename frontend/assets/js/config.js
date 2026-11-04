const API_BASE_URL = "http://127.0.0.1:5000/api";

const API_ENDPOINTS = {
    register: `${API_BASE_URL}/auth/register`,
    login: `${API_BASE_URL}/auth/login`,
    me: `${API_BASE_URL}/auth/me`,

    files: `${API_BASE_URL}/files`,
    upload: `${API_BASE_URL}/files/upload`
};