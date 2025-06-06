# Chatbot RAG Sejarah

Ini adalah proyek chatbot berbasis API yang memungkinkan pengguna berinteraksi dengan persona tokoh sejarah Indonesia (seperti Soekarno atau Mohammad Hatta) dan mendapatkan jawaban yang diperkaya konteks dari dataset sejarah menggunakan **Retrieval Augmented Generation (RAG)**. Implementasi RAG ini memanfaatkan **FAISS vector index** dan model embedding **Gemini Embedding (gemini-embedding-001)** dari Google Vertex AI untuk pencarian informasi yang efisien dan akurat.

## Fitur Utama

* **Persona Chatbot:** Respons chatbot disesuaikan dengan gaya bahasa dan kepribadian tokoh sejarah yang dipilih (saat ini: Soekarno dan Mohammad Hatta).
* **Retrieval Augmented Generation (RAG):** Menggunakan basis pengetahuan (`knowledge.txt`) yang diindeks dengan FAISS untuk menemukan konteks paling relevan terhadap pertanyaan pengguna, memastikan jawaban yang akurat, relevan, dan mengurangi halusinasi model.
* **Vector Embedding Canggih:** Memanfaatkan model `gemini-embedding-001` dari Google Vertex AI untuk mengubah teks menjadi representasi numerik (embedding) yang berkualitas tinggi.
* **Google Vertex AI Generative Model:** Menggunakan model generatif `gemini-2.0-flash` untuk pemrosesan bahasa alami dan generasi jawaban.
* **Flask API:** Menyediakan endpoint API sederhana untuk interaksi chatbot.
* **Containerized (Docker):** Aplikasi dikemas dalam Docker container untuk deployment yang mudah dan konsisten, khususnya ke Google Cloud Run.
* **Google Cloud Storage Integration:** Data basis pengetahuan, FAISS index, dan mapping disimpan dengan aman di GCS bucket.

## Alur Kerja Retrieval Augmented Generation (RAG)

Sistem RAG ini beroperasi dalam dua fase utama:

### 1. Fase Persiapan & Indeksasi (Batch / Offline)

Fase ini dilakukan sekali (atau setiap kali basis pengetahuan diperbarui) untuk menyiapkan data agar dapat dicari secara efisien. Ini ditangani oleh `build_faiss_index.py`.

1.  **Pengambilan Data:** Teks basis pengetahuan (`knowledge.txt`) diunduh dari Google Cloud Storage.
2.  **Pemecahan Teks (Chunking):** Teks panjang dibagi menjadi potongan-potongan kecil (chunks) yang lebih mudah dikelola dan memiliki batasan ukuran tertentu (misalnya, 100 kata per chunk).
3.  **Pembuatan Embedding:** Setiap chunk teks diubah menjadi vektor numerik (embedding) menggunakan model `gemini-embedding-001` dari Google Vertex AI. Embedding ini menangkap makna semantik dari teks.
4.  **Pembangunan Indeks Vektor:** Embedding dari semua chunks ditambahkan ke dalam indeks FAISS (`faiss.IndexFlatL2`). FAISS adalah library untuk pencarian kesamaan yang efisien pada kumpulan vektor yang besar.
5.  **Penyimpanan Indeks & Mapping:**
    * Indeks FAISS disimpan sebagai file (`faiss.index`).
    * File terpisah (`mapping.txt`) dibuat untuk menyimpan pemetaan dari ID numerik di indeks FAISS kembali ke teks asli dari setiap chunk.
    * Kedua file ini kemudian diunggah ke Google Cloud Storage untuk persistent storage.

### 2. Fase Runtime & Interaksi (Online / On-Demand)

Fase ini terjadi setiap kali pengguna mengirimkan pertanyaan ke chatbot. Ini ditangani oleh `main.py` dan `rag_utils.py`.

1.  **Pemuatan Indeks (Cold Start):** Saat container aplikasi Cloud Run pertama kali dimulai, `faiss.index` dan `mapping.txt` diunduh dari Google Cloud Storage dan dimuat ke memori. Ini hanya terjadi sekali per instans container.
2.  **Penerimaan Pertanyaan:** Aplikasi menerima pertanyaan dari pengguna melalui endpoint API.
3.  **Pembuatan Embedding Query:** Pertanyaan pengguna diubah menjadi vektor numerik (embedding) menggunakan model `gemini-embedding-001`. Embedding ini dirancang untuk mewakili maksud dari pertanyaan.
4.  **Pencarian Konteks Relevan (Retrieval):** Embedding pertanyaan digunakan untuk mencari `top_k` (misalnya, 3) chunk teks paling mirip di dalam FAISS index. FAISS mengembalikan ID dari chunk-chunk yang paling relevan.
5.  **Pengambilan Teks Asli:** Menggunakan `mapping.txt`, ID chunk yang relevan digunakan untuk mengambil teks asli dari basis pengetahuan.
6.  **Pembentukan Prompt:** Teks-teks relevan ini digabungkan dan ditambahkan ke prompt, bersama dengan pertanyaan asli pengguna dan instruksi persona (Soekarno/Hatta). Ini menjadi konteks yang kaya bagi model LLM.
7.  **Generasi Jawaban (Augmentation & Generation):** Prompt yang sudah diperkaya konteks dikirimkan ke model generatif `gemini-2.0-flash` dari Google Vertex AI. Model menggunakan konteks yang diberikan untuk menghasilkan jawaban yang akurat, relevan, dan sesuai dengan persona yang dipilih.
8.  **Respons API:** Jawaban yang dihasilkan dikirim kembali kepada pengguna melalui API.

## Struktur Proyek

```
.
├── main.py             # Aplikasi Flask utama, mengelola endpoint API dan interaksi LLM
├── rag_utils.py        # Utilitas untuk logika RAG (pemuatan indeks, embedding query, pencarian FAISS)
├── requirements.txt    # Daftar dependensi Python untuk aplikasi
├── Dockerfile          # Instruksi untuk membangun Docker image aplikasi
├── build_faiss_index.py # Skrip untuk membangun FAISS index dan mapping (dijalankan secara terpisah)
├── knowledge.txt       # File teks yang berisi basis pengetahuan sejarah (digunakan oleh build_faiss_index.py)
├── faiss.index         # Hasil dari build_faiss_index.py (di-upload ke GCS)
├── mapping.txt         # Hasil dari build_faiss_index.py (di-upload ke GCS)
└── README.md           # File ini
```

---