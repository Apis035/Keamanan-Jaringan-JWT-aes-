const loginForm = document.getElementById("loginForm");

if (loginForm) {
    loginForm.addEventListener("submit", async function (event) {
        event.preventDefault();

        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value;
        const message = document.getElementById("message");
        const button = document.getElementById("loginButton");

        message.className = "message";
        message.textContent = "";

        button.disabled = true;
        button.textContent = "Memproses...";

        try {
            const result = await apiRequest(API_ENDPOINTS.login, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    email: email,
                    password: password
                })
            });

            const token =
                result.access_token ||
                result.data?.access_token;

            if (!token) {
                throw new Error("Token login tidak ditemukan.");
            }

            localStorage.setItem("access_token", token);

            message.textContent = "Login berhasil!";
            message.className = "message success";

            window.location.href = "dashboard.html";

        } catch (error) {
            message.textContent = error.message;
            message.className = "message error";

        } finally {
            button.disabled = false;
            button.textContent = "Login";
        }
    });
}