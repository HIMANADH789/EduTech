from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
import ollama

VECTOR_DB_PATH = "vector_store"

# Load vector store
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectorstore = FAISS.load_local(VECTOR_DB_PATH, embeddings, allow_dangerous_deserialization=True)

def ask_question(query):
    # 1. Retrieve relevant chunks
    results = vectorstore.similarity_search(query, k=3)
    context = "\n\n".join([res.page_content for res in results])

    # 2. Create prompt for the model
    prompt = f"""
You are a highly knowledgeable NCERT Biology tutor.

Rules:

1. If the question is not strictly biology, always link it to biology relevance.
2. Do NOT hallucinate; base your answer only on the NCERT content below.



Relevant NCERT content:
{context}

Question:
{query}

Answer following the rules above.
"""

    # 3. Send to local model via Ollama
    response = ollama.chat(model="llama2", messages=[
        {"role": "user", "content": prompt}
    ])

    print("Answer:", response["message"]["content"])

if __name__ == "__main__":
    q = input("Ask a biology question: ")
    ask_question(q)
