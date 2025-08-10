import streamlit as st
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.memory import ConversationBufferMemory
import ollama

# Load vector store
VECTOR_DB_PATH = "vector_store"
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectorstore = FAISS.load_local(VECTOR_DB_PATH, embeddings, allow_dangerous_deserialization=True)

# Conversation memory
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

def ask_gpt(query):
    # Retrieve context from NCERT
    results = vectorstore.similarity_search(query, k=3)
    context = "\n\n".join([res.page_content for res in results])

    # Combine with chat history
    history_text = "\n".join([f"{m.type}: {m.content}" for m in memory.chat_memory.messages])

    prompt = f"""
    You are a helpful NCERT Biology tutor.
    Previous conversation:
    {history_text}

    Relevant textbook excerpts:
    {context}

    Question: {query}
    """

    # Get answer from Ollama model
    response = ollama.chat(model="llama2", messages=[
        {"role": "user", "content": prompt}
    ])

    answer = response["message"]["content"]
    memory.chat_memory.add_user_message(query)
    memory.chat_memory.add_ai_message(answer)
    return answer

# Streamlit UI
st.title("EduGPT — NCERT Biology Tutor")
user_input = st.text_input("Ask a question about Biology:")

if user_input:
    answer = ask_gpt(user_input)
    st.markdown(f"**Answer:** {answer}")

# Display conversation history
with st.expander("Conversation History"):
    for msg in memory.chat_memory.messages:
        st.write(f"{msg.type.capitalize()}: {msg.content}")
