function setMessage(el, text, type) {
    el.textContent = text;
    el.className = text ? `message ${type}` : "message";
}

// Jika sudah punya token, langsung ke dashboard
if (getToken() && document.querySelector(".auth-container")) {
    window.location.href = "dashboard.html";
}

const loginForm = document.getElementById("loginForm");

if (loginForm) {
    loginForm.addEventListener("submit", async function (event) {
        event.preventDefault();

        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value;
        const message = document.getElementById("message");
        const button = document.getElementById("loginButton");

        setMessage(message, "", "");

        button.disabled = true;
        button.textContent = "Memproses...";

        try {
            const result = await apiRequest(API_ENDPOINTS.login, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password })
            });

            const token = result.access_token || result.data?.access_token;

            if (!token) {
                throw new Error("Token login tidak ditemukan.");
            }

            localStorage.setItem("access_token", token);

            setMessage(message, "Login berhasil!", "success");
            window.location.href = "dashboard.html";

        } catch (error) {
            setMessage(message, error.message, "error");

        } finally {
            button.disabled = false;
            button.textContent = "Login";
        }
    });
}

const registerForm = document.getElementById("registerForm");

if (registerForm) {
    registerForm.addEventListener("submit", async function (event) {
        event.preventDefault();

        const name = document.getElementById("name").value.trim();
        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value;
        const confirm = document.getElementById("confirmPassword").value;
        const message = document.getElementById("message");
        const button = document.getElementById("registerButton");

        setMessage(message, "", "");

        if (password.length < 8) {
            setMessage(message, "Password minimal 8 karakter.", "error");
            return;
        }

        if (password !== confirm) {
            setMessage(message, "Konfirmasi password tidak sama.", "error");
            return;
        }

        button.disabled = true;
        button.textContent = "Memproses...";

        try {
            await apiRequest(API_ENDPOINTS.register, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name, email, password })
            });

            setMessage(message, "Registrasi berhasil! Mengalihkan ke login...", "success");
            registerForm.reset();

            setTimeout(() => {
                window.location.href = "login.html";
            }, 1200);

        } catch (error) {
            setMessage(message, error.message, "error");
            button.disabled = false;
            button.textContent = "Daftar";
        }
    });
}
