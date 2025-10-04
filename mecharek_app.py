import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage

# ========== 1️⃣ Page Config ==========
st.set_page_config(page_title="MechaRek — Keyboard Recommender", page_icon="⌨️", layout="wide")
st.title("⌨️ MechaRek — Mechanical Keyboard Recommender")
st.caption("Chatbot rekomendasi keyboard mechanical bertenaga Google Gemini & LangGraph")

# ========== 2️⃣ Sidebar Settings ==========
with st.sidebar:
    st.subheader("⚙️ Pengaturan")
    google_api_key = st.text_input("Masukkan Google API Key:", type="password")
    reset_button = st.button("🔄 Reset Percakapan", help="Hapus semua pesan dan mulai dari awal")

if not google_api_key:
    st.info("Masukkan API key Gemini di sidebar untuk mulai chatting.", icon="🗝️")
    st.stop()

# ========== 3️⃣ Dataset Keyboard Lokal ==========
KEYBOARDS = [
    {"nama": "Monka K75", "layout": "75%", "switch": "Star Vector (linear)", "harga": "Rp 549.000",
     "deskripsi": "Compact, solid build, cocok untuk coding dan gaming santai."},
    {"nama": "Ajazz AK33", "layout": "75%", "switch": "Brown (tactile)", "harga": "Rp 450.000",
     "deskripsi": "Tactile feel nyaman untuk mengetik lama."},
    {"nama": "Redragon K617", "layout": "60%", "switch": "Red (linear)", "harga": "Rp 650.000",
     "deskripsi": "60% keyboard gaming RGB, budget-friendly."},
    {"nama": "RK61", "layout": "60%", "switch": "Outemu Red (linear)", "harga": "Rp 550.000",
     "deskripsi": "Compact, mudah dibawa, cocok untuk laptop setup."},
    {"nama": "Keychron K6", "layout": "65%", "switch": "Gateron Red / Brown", "harga": "Rp 1.200.000",
     "deskripsi": "Wireless, hot-swappable, premium feel."},
    {"nama": "Akko 3068B", "layout": "65%", "switch": "Akko Jelly Pink (linear)", "harga": "Rp 1.350.000",
     "deskripsi": "Dual-mode wireless dengan desain estetik."}
]

def get_keyboard_list():
    text = "Berikut daftar keyboard mechanical yang dikenal MechaRek:\n"
    for kb in KEYBOARDS:
        text += f"- **{kb['nama']}** ({kb['layout']} | {kb['switch']} | {kb['harga']}) — {kb['deskripsi']}\n"
    return text

# ========== 4️⃣ Agent Initialization ==========
if ("agent" not in st.session_state) or (getattr(st.session_state, "_last_key", None) != google_api_key):
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=google_api_key,
            temperature=0.7,
        )

        prompt_instruction = (
            "Kamu adalah MechaRek, asisten AI ahli keyboard mechanical. "
            "Bantu user memilih keyboard yang cocok berdasarkan preferensi mereka "
            "(switch, layout, harga, atau kegunaan). "
            "Jawablah dengan sopan dan jelas, bisa dalam gaya santai atau formal tergantung konteks. "
            "Gunakan data internal berikut saat memberikan rekomendasi:\n\n"
            f"{get_keyboard_list()}\n\n"
            "Jika user bertanya di luar topik keyboard mechanical, jawab singkat bahwa kamu hanya ahli di bidang itu."
        )

        st.session_state.agent = create_react_agent(
            model=llm,
            tools=[],  # bisa ditambah kalau nanti mau integrasi API toko
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

# ========== 6️⃣ Display Chat History ==========
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
