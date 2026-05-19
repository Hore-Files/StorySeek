# StorySeek - React Frontend

Antarmuka (Frontend) baru untuk StorySeek, dibangun menggunakan **React**, **Vite**, dan **Tailwind CSS**. Desain aplikasi ini didasarkan pada *Design System* khusus dari proyek Stitch (ID: 12654607408661905344) yang menampilkan estetika premium bergaya *Glassmorphism*, font modern, dan antarmuka responsif.

## Prasyarat

Pastikan Anda telah menginstal:
- **Node.js** (Minimal versi 18+)
- **NPM** (Node Package Manager, otomatis terinstal bersama Node.js)

Pastikan juga **Backend FastAPI StorySeek** Anda sudah berjalan di `http://localhost:8000`.

## Cara Instalasi dan Menjalankan (Tutorial)

> **PENTING**: Semua perintah di bawah ini harus dijalankan di dalam folder `frontend-react`, bukan di *root* proyek.

### 1. Masuk ke direktori frontend
Buka terminal Anda, dan arahkan ke dalam folder `frontend-react`:
```bash
cd frontend-react
```

### 2. Instal dependensi (Paket NPM)
Jalankan perintah instalasi untuk mengunduh semua library yang dibutuhkan (React, Tailwind CSS, Lucide Icons, dll):
```bash
npm install
```
*(Catatan: Jika Anda mengalami error `ENOENT package.json` sebelumnya, itu berarti Anda menjalankan `npm install` dari luar folder `frontend-react`. Pastikan sudah melakukan `cd frontend-react` terlebih dahulu).*

### 3. Jalankan Server Development
Setelah instalasi selesai, jalankan server pengembangan (dev server) Vite:
```bash
npm run dev
```

### 4. Akses Aplikasi di Browser
Server Vite akan berjalan dan dapat diakses melalui browser di alamat berikut:
👉 **http://localhost:3000**

(Port telah diubah menjadi 3000 sesuai konfigurasi terbaru).

---

## Struktur Folder

- `src/App.jsx` — Komponen utama yang mengatur tata letak, State (kueri pencarian, filter, mode), dan memanggil API FastAPI.
- `src/components/StoryCard.jsx` — Komponen kartu desain *glassmorphism* untuk menampilkan detail fiksi/cerita hasil pencarian (menampilkan Genre, Tropes, dll).
- `src/components/SimilarStories.jsx` — Komponen rekomendasi (*More like this*) yang tersembunyi dengan efek transisi mulus.
- `tailwind.config.js` — Menyimpan seluruh *Design System Tokens* dari Stitch (Warna utama, tipografi, dan border radius).
- `vite.config.js` — Konfigurasi server development (diatur ke port 3000).

## Konfigurasi API
Secara default, frontend ini akan menembak ke backend `http://localhost:8000`. Jika backend berjalan di alamat lain, Anda dapat mengubah konstanta `BACKEND_URL` di dalam `src/App.jsx` atau menggunakan *Environment Variables* (file `.env`).
