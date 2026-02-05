import json
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document

# =========================
# Paths
# =========================
CHUNKS_FILE = Path("../data/processed/processed_chunks.json")
VECTOR_DB_PATH = Path("vector_store")

# =========================
# Load chunks
# =========================
with CHUNKS_FILE.open("r", encoding="utf-8") as f:
    chunks_data = json.load(f)

documents = []

for c in chunks_data:
    documents.append(
        Document(
            page_content=c["text"],
            metadata={
                "source": c.get("source", ""),
                "chapter": c.get("chapter", ""),
                "chunk_index": c.get("chunk_index"),
                "char_start": c.get("char_start"),
                "char_end": c.get("char_end"),
            },
        )
    )

print(f"✅ Loaded {len(documents)} documents")

# =========================
# Embeddings (STABLE)
# =========================
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# =========================
# Build FAISS (SAFE PATH)
# =========================
vectorstore = FAISS.from_documents(
    documents=documents,
    embedding=embeddings
)

# =========================
# Save
# =========================
VECTOR_DB_PATH.mkdir(parents=True, exist_ok=True)
vectorstore.save_local(VECTOR_DB_PATH)

print(f"✅ Vector store saved to: {VECTOR_DB_PATH.resolve()}")
