import os
import json
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

# === Paths ===
CHUNKS_FILE = "../data/processed/processed_chunks.json"  # output from process_clean_jsons_to_chunks.py
VECTOR_DB_PATH = "vector_store"

# === Load processed chunks ===
with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
    chunks_data = json.load(f)

texts = [c["text"] for c in chunks_data]
metadatas = [
    {
        "source": c.get("source", ""),
        "chapter": c.get("chapter", ""),
        "chunk_index": c.get("chunk_index", None),
        "char_start": c.get("char_start", None),
        "char_end": c.get("char_end", None)
    }
    for c in chunks_data
]

print(f"✅ Loaded {len(texts)} chunks from {CHUNKS_FILE}")

# === Create embeddings ===
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# === Store in FAISS with metadata ===
vectorstore = FAISS.from_texts(texts, embedding=embeddings, metadatas=metadatas)
vectorstore.save_local(VECTOR_DB_PATH)

print(f"✅ Vector store saved at: {VECTOR_DB_PATH}")
