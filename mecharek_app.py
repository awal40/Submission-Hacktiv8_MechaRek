import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage
from langchain.tools import tool
from exa_py import Exa

# ========== 1️⃣ Page Config ==========
st.set_page_config(page_title="MechaRek — Keyboard Recommender", page_icon="⌨️", layout="wide")
st.title("⌨️ MechaRek — Mechanical Keyboard Recommender")
st.caption("Chatbot rekomendasi keyboard mechanical bertenaga Google Gemini dan Exa Search API")

# ========== 2️⃣ Sidebar Settings ==========
with st.sidebar:
    st.subheader("⚙️ Pengaturan")
    google_api_key = st.text_input("Masukkan Google API Key:", type="password")
    exa_api_key = st.text_input("Masukkan Exa API Key (opsional):", type="password")
    gaya_bahasa = st.radio("🗣️ Gaya Bahasa", ["Santai", "Formal"], index=0)
    reset_button = st.button("🔄 Reset Percakapan", help="Hapus semua pesan dan mulai dari awal")

if not google_api_key:
    st.info("Masukkan API key Gemini di sidebar untuk mulai chatting.", icon="🗝️")
    st.stop()

# ========== 3️⃣ Tools Exa API ==========
@tool
def search_keyboard_info(query: str) -> str:
    """Mencari informasi keyboard (review, toko online, perbandingan) menggunakan Exa API."""
    if not exa_api_key:
        return "Exa API key belum diisi, jadi aku belum bisa mencari info online."
    try:
        exa = Exa(api_key=exa_api_key)
        results = exa.search(query, num_results=5)
        if not results.results:
            return "Tidak ada hasil ditemukan."
        output = "🔗 **Hasil pencarian dari web:**\n"
        for r in results.results:
            output += f"- [{r.title}]({r.url})\n"
        return output
    except Exception as e:
        return f"Terjadi error saat memanggil Exa API: {e}"

tools = [search_keyboard_info]

# ========== 4️⃣ Agent Initialization ==========
if ("agent" not in st.session_state) or (getattr(st.session_state, "_last_key", None) != google_api_key):
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=google_api_key,
            temperature=0.7,
        )

        gaya_instruksi = (
            "Gunakan gaya bahasa santai dan akrab seperti teman ngobrol, boleh pakai kata 'nih', 'bro', 'dong'."
            if gaya_bahasa == "Santai"
            else "Gunakan bahasa formal, sopan, profesional, dan jelas."
        )

        prompt_instruction = (
            f"Kamu adalah MechaRek, asisten AI ahli keyboard mechanical. "
            f"Tugasmu adalah membantu user memilih keyboard berdasarkan kebutuhan mereka "
            f"(gaming, kerja, coding, budget, preferensi switch). "
            f"{gaya_instruksi} "
            f"Jika user meminta review, perbandingan, atau harga terkini, gunakan tool pencarian online jika tersedia. "
            f"Jika tool tidak tersedia, berikan saran umum berdasarkan pengetahuan umummu. "
            f"Fokus hanya pada topik keyboard mechanical dan hal-hal terkait."
        )

        st.session_state.agent = create_react_agent(
            model=llm,
            tools=tools,
            prompt=prompt_instruction,
        )

        st.session_state._last_key = google_api_key
        st.session_state.pop("messages", None)
    except Exception as e:
        st.error(f"Error inisialisasi LLM: {e}")
        st.stop()

# ========== 5️⃣ Chat History ==========
if "messages" not in st.session_state:
    st.session_state.messages = []

if reset_button:
    st.session_state.pop("messages", None)
    st.session_state.pop("agent", None)
    st.rerun()

# ========== 6️⃣ Display Chat ==========
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ========== 7️⃣ Chat Input ==========
prompt = st.chat_input("Tulis pertanyaanmu... Contoh: 'rekomendasi keyboard linear 500 ribuan buat ngoding'")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        messages = []
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

        response = st.session_state.agent.invoke({"messages": messages})
        if "messages" in response and len(response["messages"]) > 0:
            answer = response["messages"][-1].content
        else:
            answer = "Maaf, aku belum bisa memberi rekomendasi."

    except Exception as e:
        answer = f"Terjadi kesalahan: {e}"

    with st.chat_message("assistant"):
        st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})
