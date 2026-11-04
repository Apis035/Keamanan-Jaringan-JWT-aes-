async function apiRequest(url, options = {}) {
    const response = await fetch(url, options);

    const contentType = response.headers.get("content-type");

    if (!response.ok) {
        let errorData = {};

        if (contentType && contentType.includes("application/json")) {
            errorData = await response.json();
        }

        throw new Error(
            errorData.message || errorData.msg || "Terjadi kesalahan pada server."
        );
    }

    if (contentType && contentType.includes("application/json")) {
        return await response.json();
    }

    return response;
}