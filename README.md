# model2-RAG

Ini adalah proyek chatbot berbasis API yang memungkinkan pengguna berinteraksi dengan persona tokoh sejarah Indonesia (seperti Soekarno atau Mohammad Hatta) dan mendapatkan jawaban yang diperkaya konteks dari dataset sejarah menggunakan Retrieval Augmented Generation (RAG) dengan model Gemini Flash dari Google Vertex AI.

## Fitur Utama

* **Persona Chatbot:** Respons chatbot disesuaikan dengan gaya bahasa dan kepribadian tokoh sejarah yang dipilih (saat ini: Soekarno dan Mohammad Hatta).
* **Retrieval Augmented Generation (RAG):** Menggunakan data sejarah yang relevan sebagai konteks untuk memastikan jawaban yang akurat, relevan, dan mengurangi halusinasi model.
* **Google Vertex AI:** Memanfaatkan kemampuan model generatif `gemini-2.0-flash-001` untuk pemrosesan bahasa alami.
* **Flask API:** Menyediakan endpoint API sederhana untuk interaksi chatbot.
* **Containerized (Docker):** Aplikasi dikemas dalam Docker container untuk deployment yang mudah dan konsisten, khususnya ke Google Cloud Run.
* **Google Cloud Storage Integration:** Data RAG disimpan dengan aman di GCS bucket.

## Struktur Proyek

```
.
├── main.py             # Aplikasi Flask utama
├── rag_utils.py        # Utilitas untuk konfigurasi RAG (jika ada fungsi RAG tambahan)
├── requirements.txt    # Daftar dependensi Python
├── Dockerfile          # Instruksi untuk membangun Docker image
├── knowledge.txt       # Contoh data teks untuk RAG corpus (Jika data RAG berbentuk file)
└── README.md           # File ini
```

## Persiapan & Deployment

Ikuti langkah-langkah di bawah ini untuk menyiapkan dan mendeploy chatbot Anda di Google Cloud.

### Prasyarat

1.  Akun Google Cloud aktif.
2.  Google Cloud SDK (gcloud CLI) terinstal dan terkonfigurasi.
3.  Docker terinstal (jika ingin mencoba secara lokal atau membangun image secara manual).
4.  Pastikan API yang diperlukan sudah aktif di proyek Google Cloud Anda (misalnya: Vertex AI API, Cloud Storage API, Cloud Run API).

### 1. Konfigurasi Proyek Google Cloud

1.  **Dapatkan Project ID Anda:**
    * Buka [Google Cloud Console](https://console.cloud.google.com/).
    * Di bagian atas, temukan Project ID Anda (misalnya, `capstonedbs`).
    * **Perbarui `PROJECT_ID` di `main.py`** dengan ID proyek Anda yang sebenarnya.

2.  **Pilih Region yang Konsisten:**
    * Pilih satu region untuk semua layanan Anda (misalnya, `us-central1` atau `asia-southeast2`). Konsistensi region penting untuk performa dan menghindari biaya transfer data lintas region.
    * **Perbarui `REGION` di `main.py`** dengan region yang Anda pilih.
    * **Pastikan GCS bucket yang digunakan untuk RAG corpus juga berada di region ini.**
    * **Pastikan deployment Cloud Run Anda juga ke region ini.**

### 2. Siapkan Data RAG (RAG Corpus)

Anda perlu membuat dan mengisi RAG Corpus di Vertex AI.

1.  **Upload Data Teks ke Cloud Storage:**
    * Buat GCS bucket baru di region yang sama dengan aplikasi Anda (misalnya, `us-central1`).
    * Pastikan bucket **TIDAK PUBLIC**.
    * Upload file `knowledge.txt` (atau file data sejarah Anda) ke bucket ini.
    * Contoh URI GCS: `gs://your-rag-data-bucket/data/knowledge.txt`

2.  **Buat RAG Corpus di Vertex AI:**
    Gunakan Cloud Shell atau lingkungan Python lokal dengan `vertexai` SDK terinstal.

    ```python
    import vertexai
    from vertexai.preview import rag

    PROJECT_ID = "YOUR_PROJECT_ID"  # Ganti dengan Project ID Anda
    REGION = "YOUR_REGION"         # Ganti dengan Region yang sama (misal: "us-central1")
    vertexai.init(project=PROJECT_ID, location=REGION)

    CORPUS_DISPLAY_NAME = "chatbot-karakter-corpus" # Nama corpus yang sama dengan di main.py
    GCS_SOURCE_URI = "gs://your-rag-data-bucket/data/" # Ganti dengan URI folder GCS Anda

    # Membuat corpus
    new_corpus = rag.create_corpus(
        display_name=CORPUS_DISPLAY_NAME,
        description="Corpus berisi informasi sejarah Indonesia untuk chatbot.",
    )
    print(f"Corpus '{new_corpus.display_name}' created with name: {new_corpus.name}")

    # Menambahkan data ke corpus
    # new_corpus.name akan dalam format projects/PROJECT_ID/locations/REGION/ragCorpora/CORPUS_ID
    add_data_response = rag.add_rag_files(
        rag_corpus=new_corpus.name,
        gcs_source=rag.GcsSource(uris=[GCS_SOURCE_URI + "**"]), # ** untuk semua file di folder & subfolder
    )
    print(f"Started adding data to corpus. Operation ID: {add_data_response.operation.name}")
    # Tunggu hingga operasi selesai
    # from google.api_core.operation import Operation
    # op = Operation(name=add_data_response.operation.name, client=rag._client)
    # op.result()
    ```
    Catat nama corpus yang dihasilkan (format `projects/PROJECT_ID/locations/REGION/ragCorpora/CORPUS_ID`). Anda akan membutuhkan `CORPUS_ID` untuk konfigurasi RAG Anda. Pastikan `CORPUS_NAME` di `main.py` sesuai.

### 3. Berikan Izin IAM untuk Service Account Vertex AI

Service Account Vertex AI Anda perlu izin untuk membaca data dari GCS bucket RAG Anda.

1.  **Temukan Nomor Proyek Anda:** Buka [Google Cloud Console](https://console.cloud.google.com/), lihat di bagian atas.
2.  **Service Account Vertex AI:** Formatnya adalah `service-<Nomor Proyek Anda>@gcp-sa-aiplatform.iam.gserviceaccount.com`.
3.  **Berikan Izin di GCS Bucket:**
    * Di Console, navigasi ke **Cloud Storage > Buckets**.
    * Klik nama *bucket* Anda (`your-rag-data-bucket`).
    * Pergi ke tab **"Permissions"**.
    * Klik **"+ ADD PRINCIPAL"**.
    * Masukkan alamat *service account* Vertex AI Anda.
    * Pilih role: `Cloud Storage` > **`Storage Object Viewer`**.
    * Klik **"SAVE"**.

### 4. Deploy Aplikasi ke Google Cloud Run

1.  **Pastikan `requirements.txt` Anda lengkap:**
    ```
    flask
    vertexai
    gunicorn
    ```
    *(Tambahkan dependensi lain yang mungkin Anda gunakan)*

2.  **Buat Dockerfile** (jika belum ada, gunakan yang sudah kita bahas):
    ```dockerfile
    FROM python:3.11-slim

    WORKDIR /app

    COPY requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt

    COPY . .

    ENV PORT 8080
    CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app
    ```

3.  **Bangun dan Push Docker Image:**
    Gunakan Cloud Shell atau terminal lokal. Pastikan Anda berada di direktori proyek Anda.

    ```bash
    # Ganti capstonedbs dengan Project ID Anda
    docker build -t gcr.io/capstonedbs/chatbot-character .
    docker push gcr.io/capstonedbs/chatbot-character
    ```

4.  **Deploy ke Cloud Run:**
    ```bash
    gcloud run deploy chatbot-character \
        --image gcr.io/capstonedbs/chatbot-character \
        --platform managed \
        --region us-central1 \ # Ganti dengan Region yang sama dengan Vertex AI Anda
        --allow-unauthenticated \
        --project capstonedbs # Ganti dengan Project ID Anda
    ```
    * `--allow-unauthenticated`: Membuat endpoint API Anda dapat diakses secara publik (tanpa memerlukan otentikasi). Ini hanya berlaku untuk *endpoint* web Anda, **bukan data di GCS bucket Anda.**

### 5. Uji Coba Chatbot Anda

Setelah deployment selesai, Anda akan mendapatkan `Service URL` seperti: `https://chatbot-character-xxxxxxxxxx-ll.a.run.app`.

Anda bisa menguji API ini menggunakan alat seperti `curl`, Postman, atau aplikasi web/mobile.

**Contoh panggilan API (gunakan `curl` di terminal):**

```bash
curl -X POST -H "Content-Type: application/json" \
     -d '{
           "karakter": "soekarno",
           "prompt": "Siapa Soekarno?"
         }' \
     YOUR_CLOUD_RUN_SERVICE_URL/chat
```
Ganti `YOUR_CLOUD_RUN_SERVICE_URL` dengan URL yang Anda dapatkan dari deployment Cloud Run.

---

