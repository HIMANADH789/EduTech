# # from langchain.vectorstores import FAISS
# # from langchain.embeddings import HuggingFaceEmbeddings

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

# === Paths ===
VECTOR_DB_PATH = "vector_store"

# === Load embeddings & vector store ===
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectorstore = FAISS.load_local(
    VECTOR_DB_PATH,
    embeddings,
    allow_dangerous_deserialization=True
)

# === Test query ===
query = "Explain medical termination of pregnancy"
results = vectorstore.similarity_search(query, k=3)  # get top 3 matches

for i, res in enumerate(results, start=1):
    meta = res.metadata
    chapter = meta.get("chapter", "N/A")
    source = meta.get("source", "N/A")
    chunk_index = meta.get("chunk_index", "N/A")

    print(f"--- Result {i} ---")
    print(f"Source: {source} | Chapter: {chapter} | Chunk: {chunk_index}")
    print(res.page_content[:300])  # preview first 300 chars
    print()
