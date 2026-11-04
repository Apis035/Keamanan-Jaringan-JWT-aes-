# SecureVault Frontend

HTML + CSS + JavaScript murni (tanpa build tool).

## Menjalankan

CORS di backend hanya mengizinkan origin `http://localhost:5173`, jadi sajikan frontend di port itu:

```bash
cd frontend
python -m http.server 5173
```

Buka http://localhost:5173 (pakai `localhost`, bukan `127.0.0.1`, supaya cocok dengan CORS).
Backend: `cd backend && python run.py` (port 5000).

## Struktur

- `pages/login.html`, `register.html`, `dashboard.html`
- `assets/js/config.js` – URL API; `api.js` – helper fetch + token; `auth.js` – login/register;
  `files.js` – upload/unduh/hapus; `dashboard.js` – UI dashboard
