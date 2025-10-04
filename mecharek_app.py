import streamlit as st
from datetime import datetime
import re
import json

st.set_page_config(page_title="MechaRek — Mechanical Keyboard Recommender", layout="wide")

# ---------------------------
# Minimal dataset (local)
# ---------------------------
KEYBOARDS = [
    {
        "name": "Monka K75",
        "layout": "75%",
        "switch": "Star Vector (linear)",
        "price_idr": 549000,
        "use_case": ["ngoding", "umum"],
        "desc": "75% compact, build solid, linear feel. Budget friendly."
    },
    {
        "name": "RK61",
        "layout": "60%",
        "switch": "Outemu Red (linear)",
        "price_idr": 550000,
        "use_case": ["gaming", "ngoding"],
        "desc": "60% compact, great for small desk and portability."
    },
    {
        "name": "Keychron K6",
        "layout": "65%",
        "switch": "Gateron Red (linear) / Brown (tactile) options",
        "price_idr": 1200000,
        "use_case": ["ngoding", "productivity"],
        "desc": "Wireless option, hot-swap, versatile for work and play."
    },
    {
        "name": "Ajazz AK33",
        "layout": "75%",
        "switch": "Brown (tactile)",
        "price_idr": 450000,
        "use_case": ["ngoding", "umum"],
        "desc": "Compact 75% with tactile switches and reasonable price."
    },
    {
        "name": "Redragon K617",
        "layout": "60%",
        "switch": "Red (linear)",
        "price_idr": 650000,
        "use_case": ["gaming", "umum"],
        "desc": "Budget gaming 60% with RGB features."
    },
    {
        "name": "Ducky One 2 (TKL)",
        "layout": "80% (TKL)",
        "switch": "Cherry MX Brown (tactile)",
        "price_idr": 2000000,
        "use_case": ["ngoding", "professional"],
        "desc": "High quality switches and stabilizers, premium typing feel."
    },
]

# ---------------------------
# Helpers: parsing & filtering
# ---------------------------
def parse_preferences(text):
    """Extract simple preferences from free text: budget (IDR), switch type, layout, use_case keywords."""
    text_l = text.lower()
    pref = {
        "switch": None,  # 'linear','tactile','clicky'
        "layout": None,  # '60%','65%','75%','tkl','full'
        "budget_idr": None,
        "use_case": None,  # 'ngoding','gaming','umum','professional'
        "explicit": text,
    }

    # detect switch type
    if any(k in text_l for k in ["linear", "linearnya", "red", "gateron red", "outemu red"]):
        pref["switch"] = "linear"
    elif any(k in text_l for k in ["tactile", "brown", "tactil"]):
        pref["switch"] = "tactile"
    elif any(k in text_l for k in ["clicky", "blue", "click"]):
        pref["switch"] = "clicky"

    # layout detection
    if "60%" in text_l or "60 persen" in text_l:
        pref["layout"] = "60%"
    elif "65%" in text_l or "65 persen" in text_l:
        pref["layout"] = "65%"
    elif "75%" in text_l or "75 persen" in text_l:
        pref["layout"] = "75%"
    elif "tkl" in text_l or "80%" in text_l:
        pref["layout"] = "80% (TKL)"
    elif "full" in text_l or "fullsize" in text_l:
        pref["layout"] = "full"

    # use_case detection
    if any(k in text_l for k in ["ngoding", "programming", "coding"]):
        pref["use_case"] = "ngoding"
    elif any(k in text_l for k in ["gaming", "game"]):
        pref["use_case"] = "gaming"
    elif any(k in text_l for k in ["kantor", "office", "professional"]):
        pref["use_case"] = "professional"
    else:
        pref["use_case"] = "umum"

    # budget detection (IDR). capture numbers like '500k', '500 ribu', '1.2juta', '1200000'
    # Handle formats: "500k", "500 rb", "500 ribu", "1.2 juta"
    m = re.search(r'(\d+[.,]?\d*)\s*(k|rb|ribu|juta|jt|m|miliar)?', text_l)
    if m:
        num = float(m.group(1).replace(",", "."))
        unit = (m.group(2) or "").lower()
        if unit in ["k", "rb", "ribu"]:
            pref["budget_idr"] = int(num * 1000)
        elif unit in ["juta", "jt"]:
            pref["budget_idr"] = int(num * 1_000_000)
        elif unit in ["m", "miliar"]:
            pref["budget_idr"] = int(num * 1_000_000_000)
        else:
            # if no unit but reasonable small (<= 10000) assume thousands?
            if num <= 10000:
                pref["budget_idr"] = int(num)  # assume user typed full number
            else:
                pref["budget_idr"] = int(num)

    return pref

def filter_keyboards(prefs, top_n=5):
    """Filter local dataset based on parsed preferences, return ranked list."""
    results = []
    for kb in KEYBOARDS:
        score = 0
        # switch
        if prefs.get("switch"):
            if prefs["switch"] in kb["switch"].lower():
                score += 30
        # layout
        if prefs.get("layout"):
            if prefs["layout"].split()[0] in kb["layout"]:
                score += 20
        # use_case
        if prefs.get("use_case"):
            if prefs["use_case"] in kb["use_case"]:
                score += 25
        # budget
        if prefs.get("budget_idr"):
            if kb["price_idr"] <= prefs["budget_idr"]:
                score += 25
            else:
                # penalize by how far over budget
                diff = kb["price_idr"] - prefs["budget_idr"]
                score -= min(25, int(diff / 100000))  # small penalty
        # base score for popularity
        score += 5
        results.append((score, kb))
    # sort desc by score
    results_sorted = sorted(results, key=lambda x: x[0], reverse=True)
    return [r[1] for r in results_sorted[:top_n]]

# ---------------------------
# LLM integration placeholder
# ---------------------------
def call_llm(api_key, provider, system_instruction, user_prompt, context=None):
    """
    Placeholder wrapper to call a real LLM.
    Currently RETURNS None (meaning: no real call).
    To enable real calls, replace the body with provider-specific code:
    - provider == "openai": use openai.ChatCompletion.create(...) or openai.chat.completions
    - provider == "genai": use google.genai client (see provider docs)

    Example (OpenAI, pseudocode):
        import openai
        openai.api_key = api_key
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role":"system","content":system_instruction}, {"role":"user","content":user_prompt}],
            temperature=0.4,
        )
        return resp["choices"][0]["message"]["content"]

    Example (Google GenAI, pseudocode):
        from google import genai
        client = genai.Client(api_key=api_key)
        chat = client.chat.create(model="gemini-1.5", messages=[...])
        return chat.last_response.content

    For safety/portability in this submission, we KEEP THIS AS A PLACEHOLDER.
    """
    # Return None to indicate "no real LLM call made"
    return None

# ---------------------------
# Streamlit UI & App logic
# ---------------------------
st.title("🛠️ MechaRek — Mechanical Keyboard Recommender")
st.caption("Bantuan memilih mechanical keyboard berdasarkan preferensi. (Hybrid: mock + LLM-ready)")

# Sidebar controls
with st.sidebar:
    st.header("Settings & Controls")
    provider = st.selectbox("LLM Provider (opsional)", ["(none)", "OpenAI (ChatGPT)", "Google GenAI (Gemini)"])
    api_key = st.text_input("API Key (optional)", type="password",
                            help="Isi jika ingin mengaktifkan pemanggilan model LLM nyata.")
    style = st.radio("Gaya bahasa", ["Santai", "Formal"])
    st.markdown("---")
    st.subheader("Session")
    if "memory" not in st.session_state:
        st.session_state.memory = {"prefs": {}, "history": []}
    if st.button("Reset Conversation & Memory"):
        st.session_state.pop("messages", None)
        st.session_state.memory = {"prefs": {}, "history": []}
        st.experimental_rerun()
    st.markdown("---")
    st.info("Workflow: masukkan preferensi di chat (contoh: 'cari keyboard linear 500rb untuk ngoding') atau gunakan bahasa natural.")

# Initialize messages
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Halo! Aku MechaRek — kamu sedang cari mechanical keyboard? Coba beri preferensimu: budget, switch (linear/tactile/clicky), layout (60%/75%/TKL), dan penggunaan (ngoding/gaming)."}
    ]

# Show memory summary
with st.expander("Memory (session)"):
    st.write("Preferences saved this session:")
    st.write(st.session_state.memory.get("prefs", {}))
    st.write("Conversation history length:", len(st.session_state.messages))

# Render messages
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.markdown(msg["content"])
    else:
        with st.chat_message("assistant"):
            st.markdown(msg["content"])

# Chat input
user_input = st.chat_input("Tulis preferensi atau tanya rekomendasi keyboard...")

def format_recommendation_response(recs, prefs, style):
    """Generate a formatted textual response from recommendation list and chosen style."""
    if not recs:
        base = "Maaf, aku belum menemukan keyboard yang cocok dengan preferensimu."
        if style == "Formal":
            return base + " Cobalah ubah rentang harga atau tipe switch."
        else:
            return base + " Coba longgarkan budget atau ganti tipe switch, ya."
    lines = []
    header = "Berikut rekomendasi yang cocok untukmu:" if style == "Formal" else "Ini dia rekomendasi yang cocok nih:"
    lines.append(header)
    for kb in recs:
        price = f"Rp {kb['price_idr']:,}".replace(",", ".")
        lines.append(f"• **{kb['name']}** — {kb['layout']} — {kb['switch']} — {price}")
        # short description
        lines.append(f"  _{kb['desc']}_")
    # suggestion
    if style == "Formal":
        lines.append("\nJika Anda ingin, saya dapat mencari review atau link pembelian untuk salah satu pilihan di atas.")
    else:
        lines.append("\nMau aku carikan link beli atau review buat salah satu pilihan di atas?")
    return "\n\n".join(lines)

# Process user input
if user_input:
    # store user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    # parse preferences
    prefs = parse_preferences(user_input)
    # save to memory (simple heuristic: if user mentions 'ingat' or 'prefer' or 'suka')
    if any(k in user_input.lower() for k in ["ingat", "simpan", "prefer", "suka", "favorit"]):
        # add to memory
        st.session_state.memory["prefs"].update(prefs)
        mem_msg = "Baik, aku akan ingat preferensimu untuk sesi ini."
        st.session_state.messages.append({"role": "assistant", "content": mem_msg})
    else:
        # choose mode: real LLM (if api_key+provider selected) else mock filtering
        assistant_text = None
        if api_key and provider != "(none)":
            # Build a system instruction & prompt to the LLM
            system_instruction = (
                f"You are MechaRek, an assistant recommending mechanical keyboards. "
                f"User preferences: {json.dumps(prefs)}. "
                f"Format: Provide 3 concise recommendations with price (IDR) and one-sentence rationale."
            )
            user_prompt = user_input
            # Call LLM via wrapper (placeholder)
            llm_resp = call_llm(api_key=api_key, provider=provider, system_instruction=system_instruction, user_prompt=user_prompt, context=st.session_state.get("messages"))
            if llm_resp:
                assistant_text = llm_resp
            else:
                # If LLM call not implemented or failed, fallback to local recommendation
                recs = filter_keyboards(prefs)
                assistant_text = ("[FALLBACK: LLM unavailable or not configured]\n\n" + format_recommendation_response(recs, prefs, style))
        else:
            # Mock mode: use local dataset filter + formatted response
            recs = filter_keyboards(prefs)
            assistant_text = format_recommendation_response(recs, prefs, style)

        # append assistant response
        st.session_state.messages.append({"role": "assistant", "content": assistant_text})
        # record memory (store last prefs)
        st.session_state.memory["prefs"] = prefs
        st.session_state.memory["history"].append({"query": user_input, "time": datetime.now().isoformat()})

    # rerender by forcing a re-run (Streamlit will show appended messages on top loop)
    st.experimental_rerun()

# Bottom controls (export)
st.markdown("---")
col1, col2 = st.columns([1, 1])
with col1:
    if st.button("Download conversation (.txt)"):
        export_text = "\n\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
        st.download_button("Klik untuk download .txt", data=export_text, file_name="mecharek_conversation.txt")
with col2:
    if st.button("Snapshot / Screenshot Guide"):
        st.info("Simpan 3 screenshot: 1) main chat (contoh percakapan), 2) sidebar (settings), 3) memory expander. Nama file: ui_main.png, ui_sidebar.png, ui_memory.png")



