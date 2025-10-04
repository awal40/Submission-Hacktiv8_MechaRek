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
    reset_button = st.button("🔄 Reset Percakapan", help="Hapus semua pesan dan mulai dari awal")

if not google_api_key:
    st.info("Masukkan API key Gemini di sidebar untuk mulai chatting.", icon="🗝️")
    st.stop()

# ========== 3️⃣ Dataset Keyboard Lokal ==========
KEYBOARDS = [
    {"nama": "Monka K75", "layout": "75%", "switch": "Star Vector (linear)", "harga": 549000,
     "deskripsi": "Compact, solid build, cocok untuk coding dan gaming santai."},
    {"nama": "Ajazz AK33", "layout": "75%", "switch": "Brown (tactile)", "harga": 450000,
     "deskripsi": "Tactile feel nyaman untuk mengetik lama."},
    {"nama": "Redragon K617", "layout": "60%", "switch": "Red (linear)", "harga": 650000,
     "deskripsi": "60% keyboard gaming RGB, budget-friendly."},
    {"nama": "RK61", "layout": "60%", "switch": "Outemu Red (linear)", "harga": 550000,
     "deskripsi": "Compact, mudah dibawa, cocok untuk laptop setup."},
    {"nama": "Keychron K6", "layout": "65%", "switch": "Gateron Red/Brown", "harga": 1200000,
     "deskripsi": "Wireless, hot-swappable, premium feel."},
    {"nama": "Akko 3068B", "layout": "65%", "switch": "Akko Jelly Pink (linear)", "harga": 1350000,
     "deskripsi": "Dual-mode wireless dengan desain estetik."}
]

def get_keyboard_list():
    text = "Berikut daftar keyboard mechanical yang dikenal MechaRek:\n"
    for kb in KEYBOARDS:
        text += f"- {kb['nama']} ({kb['layout']} | {kb['switch']} | Rp {kb['harga']:,}) — {kb['deskripsi']}\n"
    return text

# ========== 4️⃣ Tools Lokal & Exa API ==========

@tool
def get_best_keyboard_by_budget(budget: int) -> str:
    """Mengembalikan daftar keyboard di bawah budget tertentu (dalam Rupiah)."""
    hasil = [kb for kb in KEYBOARDS if kb["harga"] <= budget]
    if not hasil:
        return f"Tidak ada keyboard di bawah Rp {budget:,}."
    teks = f"🎯 Keyboard di bawah Rp {budget:,}:\n"
    for kb in hasil:
        teks += f"- {kb['nama']} ({kb['layout']} | {kb['switch']} | Rp {kb['harga']:,})\n"
    return teks

@tool
def get_switch_info(switch_type: str) -> str:
    """Memberikan penjelasan tentang tipe switch tertentu (linear/tactile/clicky)."""
    t = switch_type.lower()
    if "linear" in t:
        return "Linear switch terasa halus tanpa feedback tactile. Cocok untuk gaming atau mengetik cepat."
    elif "tactile" in t:
        return "Tactile switch punya bump halus tiap tekan. Nyaman untuk mengetik lama tanpa suara bising."
    elif "clicky" in t:
        return "Clicky switch menghasilkan bunyi klik jelas dan feedback kuat, disukai penggemar suara klasik."
    else:
        return "Jenis switch tidak dikenali. Coba sebut linear, tactile, atau clicky."

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

tools = [get_best_keyboard_by_budget, get_switch_info, search_keyboard_info]

# ========== 5️⃣ Agent Initialization ==========
if ("agent" not in st.session_state) or (getattr(st.session_state, "_last_key", None) != google_api_key):
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=google_api_key,
            temperature=0.6,
        )

        prompt_instruction = (
            "Kamu adalah MechaRek, asisten AI ahli keyboard mechanical. "
            "Tugasmu adalah membantu user memilih keyboard berdasarkan preferensi (switch, layout, harga, atau kegunaan). "
            "Gunakan gaya bahasa yang ramah, tapi tetap informatif. "
            "Kamu bisa memakai tool yang tersedia jika perlu data tambahan.\n\n"
            f"Data internal keyboard:\n{get_keyboard_list()}\n\n"
            "Jika pertanyaan user tidak relevan dengan keyboard, jawab singkat bahwa kamu hanya fokus pada topik itu."
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

# ========== 6️⃣ Chat History ==========
if "messages" not in st.session_state:
    st.session_state.messages = []

if reset_button:
    st.session_state.pop("messages", None)
    st.session_state.pop("agent", None)
    st.rerun()

# ========== 7️⃣ Display Chat ==========
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ========== 8️⃣ Chat Input ==========
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
