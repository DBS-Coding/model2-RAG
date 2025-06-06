from google.cloud import storage, aiplatform
from vertexai.language_models import TextEmbeddingModel 
import faiss
import os
import numpy as np
import uuid

PROJECT_ID = "capstonedbs"
LOCATION = "us-central1" 
BUCKET_NAME = "sejarah" 
FILE_NAME = "knowledge.txt"
INDEX_FILE_NAME = "faiss.index"

aiplatform.init(project=PROJECT_ID, location=LOCATION)

def download_knowledge():
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(FILE_NAME)
    return blob.download_as_text()

def split_text(text, max_words=100):
    sentences = text.split('.')
    chunks = []
    chunk = ""
    for sentence in sentences:
        if not sentence.strip():
            continue
        
        if len((chunk + sentence).split()) > max_words:
            chunks.append(chunk.strip())
            chunk = sentence.strip() + "."
        else:
            chunk += sentence.strip() + "."
    if chunk:
        chunks.append(chunk.strip())
    return chunks


def get_embeddings(text_list):
    model = TextEmbeddingModel.from_pretrained("gemini-embedding-001")
    embeddings = []

    for text in text_list:
        try:
            embedding = model.get_embeddings([text])[0].values
            embeddings.append(embedding)
        except Exception as e:
            print(f"Error saat membuat embedding untuk teks: '{text[:100]}...' - {e}")
            raise

    if not embeddings:
        raise ValueError("Tidak ada embeddings yang berhasil dihasilkan.")

    return np.array(embeddings, dtype=np.float32)

def build_index():
    text = download_knowledge()
    chunks = split_text(text)
    
    if not chunks:
        raise ValueError("Tidak ada chunks yang dihasilkan dari knowledge.txt. Pastikan file tidak kosong atau formatnya benar.")

    embeddings = get_embeddings(chunks)

    if len(embeddings) == 0:
        raise ValueError("Tidak ada embeddings yang dihasilkan. Mungkin ada masalah dengan file knowledge.txt atau panggilan API.")
    
    dim = len(embeddings[0]) 
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    faiss.write_index(index, INDEX_FILE_NAME)
    return chunks

def upload_to_gcs(local_file, blob_name):
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(local_file)

if __name__ == "__main__":
    try:
        print("Memulai proses pembuatan indeks FAISS...")
        chunks = build_index()
        
        if chunks:
            print(f"Berhasil membuat {len(chunks)} chunks dan embeddings.")
            print(f"Mengupload {INDEX_FILE_NAME} ke GCS...")
            upload_to_gcs(INDEX_FILE_NAME, INDEX_FILE_NAME)

            print("Membuat dan mengupload mapping.txt ke GCS...")
            with open("mapping.txt", "w", encoding="utf-8") as f: # Tambahkan encoding
                for i, chunk in enumerate(chunks):
                    f.write(f"{i}|{chunk}\n")
            upload_to_gcs("mapping.txt", "mapping.txt")

            print("Index dan mapping berhasil dibuat dan diupload.")
        else:
            print("Tidak ada chunks yang diproses, index dan mapping tidak dibuat atau diupload.")
            
    except Exception as e:
        print(f"Terjadi kesalahan fatal: {e}")