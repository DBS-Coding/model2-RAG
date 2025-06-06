from google.cloud import storage
import faiss
import numpy as np
import os
from google.cloud import aiplatform
from vertexai.language_models import TextEmbeddingModel

PROJECT_ID = "capstonedbs"
LOCATION = "us-central1"
BUCKET_NAME = "sejarah" 
INDEX_FILE_NAME = "faiss.index"
MAPPING_FILE_NAME = "mapping.txt"

aiplatform.init(project=PROJECT_ID, location=LOCATION)
embedding_model = None
faiss_index = None
chunks_mapping = {}

def load_faiss_index_and_mapping():
    global faiss_index, chunks_mapping, embedding_model
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)

    index_blob = bucket.blob(INDEX_FILE_NAME)
    index_blob.download_to_filename(INDEX_FILE_NAME)
    faiss_index = faiss.read_index(INDEX_FILE_NAME)
    print(f"FAISS index '{INDEX_FILE_NAME}' berhasil dimuat.")

    mapping_blob = bucket.blob(MAPPING_FILE_NAME)
    mapping_blob.download_to_filename(MAPPING_FILE_NAME)
    
    with open(MAPPING_FILE_NAME, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split('|', 1) # Split hanya pada '|' pertama
            if len(parts) == 2:
                try:
                    idx = int(parts[0])
                    text = parts[1]
                    chunks_mapping[idx] = text
                except ValueError as e:
                    print(f"Peringatan: Gagal mem-parse baris mapping: {line.strip()}. Error: {e}")
            else:
                print(f"Peringatan: Baris mapping tidak valid: {line.strip()}")
    print(f"Mapping '{MAPPING_FILE_NAME}' berhasil dimuat.")
    
    embedding_model = TextEmbeddingModel.from_pretrained("gemini-embedding-001")
    print("Model embedding 'gemini-embedding-001' berhasil diinisialisasi.")

def get_query_embedding(query_text):
    """Mendapatkan embedding untuk query."""
    global embedding_model
    if embedding_model is None:
        embedding_model = TextEmbeddingModel.from_pretrained("gemini-embedding-001")
        print("Model embedding diinisialisasi ulang (query).")
    try:
        embedding = embedding_model.get_embeddings([query_text])[0].values
        return np.array(embedding, dtype=np.float32).reshape(1, -1)
    except Exception as e:
        print(f"Error saat membuat embedding untuk query: '{query_text[:50]}...' - {e}")
        raise

def retrieve_context(query_embedding, top_k=3):
    """Mencari konteks relevan di FAISS index."""
    global faiss_index, chunks_mapping
    if faiss_index is None or not chunks_mapping:
        load_faiss_index_and_mapping()

    D, I = faiss_index.search(query_embedding, top_k) 
    
    relevant_contexts = []
    for idx in I[0]:
        if idx in chunks_mapping:
            relevant_contexts.append(chunks_mapping[idx])
        else:
            print(f"Peringatan: Index {idx} tidak ditemukan di mapping.")
    return "\n\n".join(relevant_contexts) 

def get_context_from_gcs(bucket_name_unused, file_name_unused, karakter, question):
    """
    Mengambil konteks relevan dari FAISS index berdasarkan pertanyaan.
    Parameter bucket_name dan file_name tidak lagi digunakan secara langsung
    untuk mengambil teks dari knowledge.txt, tetapi tetap diterima
    untuk kompatibilitas dengan main.py.
    """
    global faiss_index, chunks_mapping

    if faiss_index is None or not chunks_mapping:
        load_faiss_index_and_mapping()

    query_embed = get_query_embedding(question)
    context = retrieve_context(query_embed, top_k=3) 

    if karakter.lower() == "soekarno":
        role_prompt = (
            "Jawablah sebagai Soekarno, Presiden pertama Indonesia. "
            "Gunakan gaya bahasa yang berapi-api, penuh semangat nasionalisme dan retorika politik.\n"
            "Buat jawaban tidak lebih dari 3 kalimat yang padat dan menggugah.\n"
        )
    elif karakter.lower() == "hatta":
        role_prompt = (
            "Jawablah sebagai Mohammad Hatta, Bapak Koperasi Indonesia. "
            "Gunakan gaya bahasa yang tenang, intelektual, dan diplomatis.\n"
            "Buat jawaban tidak lebih dari 3 kalimat yang ringkas dan informatif.\n"
        )
    else:
        role_prompt = "Jawablah dengan berdasarkan konteks berikut.\n"

    prompt = f"""{role_prompt}
Berikut adalah konteks sejarah yang relevan:

{context}

Pertanyaan:
{question}
"""

    return prompt

if __name__ == "__main__":
    print("Menguji rag_utils secara terpisah...")
    load_faiss_index_and_mapping()
    test_question = "Siapa itu Soekarno?"
    final_prompt = get_context_from_gcs("dummy_bucket", "dummy_file", "none", test_question)
    print("\nPrompt yang dihasilkan untuk LLM:")
    print(final_prompt)