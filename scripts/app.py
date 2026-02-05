import warnings
warnings.filterwarnings("ignore")

import streamlit as st
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import Ollama
from langchain.memory import ConversationBufferMemory

# -------------------------
# Config
# -------------------------
VECTOR_DB_PATH = "vector_store"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
OLLAMA_MODEL = "llama2"

# -------------------------
# Embeddings
# -------------------------
embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL
)

# -------------------------
# Load FAISS (Rebuilt safe)
# -------------------------
# Remove 'allow_dangerous_deserialization' argument
# ⚠️ Rebuild vector store if old pickle is incompatible
try:
    vectorstore = FAISS.load_local(
        VECTOR_DB_PATH,
        embeddings
    )
except Exception:
    st.warning("FAISS index incompatible. Rebuilding vector store...")
    from scripts.build_vectorstore import build_vectorstore
    vectorstore = build_vectorstore(embeddings, VECTOR_DB_PATH)

# -------------------------
# LLM
# -------------------------
llm = Ollama(model=OLLAMA_MODEL)

# -------------------------
# Memory
# -------------------------
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

# -------------------------
# RAG Logic
# -------------------------
def ask_rag(query: str) -> str:
    docs = vectorstore.similarity_search(query, k=3)
    context = "\n\n".join(doc.page_content for doc in docs)

    history = "\n".join(
        f"{m.type}: {m.content}"
        for m in memory.chat_memory.messages
    )

    prompt = f"""You are a helpful NCERT Biology tutor.

Conversation so far:
{history}

Relevant NCERT content:
{context}

Question:
{query}
explain the concept clearly for a 15-year-old using simple analogies and step-by-step reasoning.
.
"""

    response = llm(prompt)

    memory.chat_memory.add_user_message(query)
    memory.chat_memory.add_ai_message(response)

    return response

# -------------------------
# Streamlit UI
# -------------------------
st.set_page_config(
    page_title="EduGPT",
    layout="centered"
)

st.title("📘 EduGPT — NCERT Biology Tutor")

query = st.text_input("Ask a biology question:")

if query:
    answer = ask_rag(query)
    st.markdown("### Answer")
    st.write(answer)

with st.expander("Conversation History"):
    for msg in memory.chat_memory.messages:
        st.write(f"**{msg.type.capitalize()}**: {msg.content}")
