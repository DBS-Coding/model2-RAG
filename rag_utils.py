from google.cloud import storage

def get_context_from_gcs(bucket_name, file_name, karakter, question):
    client = storage.Client()
    bucket = client.get_bucket(bucket_name)
    blob = bucket.blob(file_name)
    text = blob.download_as_text()

    if karakter.lower() == "soekarno":
        role_prompt = (
            "Jawablah sebagai Soekarno, Presiden pertama Indonesia. "
            "Gunakan gaya bahasa yang berapi-api, penuh semangat nasionalisme dan retorika politik.\n"
        )
    elif karakter.lower() == "hatta":
        role_prompt = (
            "Jawablah sebagai Mohammad Hatta, Bapak Koperasi Indonesia. "
            "Gunakan gaya bahasa yang tenang, intelektual, dan diplomatis.\n"
        )
    else:
        role_prompt = "Jawablah dengan berdasarkan konteks berikut.\n"

    prompt = f"""{role_prompt}
Berikut adalah konteks sejarah:

{text}

Pertanyaan:
{question}
"""

    return prompt
