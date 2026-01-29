import os  # delo z okoljskimi spremenljivkami (lokalno) in splošne OS funkcije
import streamlit as st  # UI elementi za spletno aplikacijo
from groq import Groq  # odjemalec za Groq API (LLM)

# -----------------------------
# 1) OSNOVNE NASTAVITVE STRANI
# -----------------------------
st.set_page_config(
    page_title="Pametni pomočnik (chatbot)",
    page_icon="💬",
    layout="centered"
)

st.title("💬 Pametni pomočnik")
st.caption("Odgovarjam izključno v slovenščini in samo o vsebini te spletne strani/projekta.")

# ------------------------------------------------------
# 2) SPECIALIZACIJA (TU NASTAVI SVOJO TEMO / OBSEG)
# ------------------------------------------------------
# Opis domene (naj bo 100% usklajen s tvojo spletno stranjo).
DOMENA = """
Sem podporni chatbot za spletno stran/projekt:
- Tema: tehnična podpora in informacije o mojem produktu / storitvi (npr. Aquanova ali Kavarna Juli).
- Odgovarjam samo o funkcionalnostih, uporabi, pogostih vprašanjih, naročanju, težavah, kontaktih, uporabi strani.
- Če vprašanje ni povezano s to temo, vljudno zavrnem.
"""

# Pravila pogovora (pomembno za “specializacijo” + slovenščino + lep stil).
PRAVILA = """
Pravila:
1) Odgovarjaj IZKLJUČNO v slovenščini.
2) Če vprašanje ni povezano z domeno, vljudno povej, da za to področje nimaš informacij, in predlagaj, naj uporabnik vpraša kaj v domeni.
3) Odgovori naj bodo kratki, pregledni, slovnično pravilni.
4) Uporabljaj alineje, kadar naštevaš korake ali možnosti.
5) Ne izmišljaj si dejstev. Če nekaj ni znano, povej, kaj potrebuješ (npr. "povejte, katero stran/izdelek mislite").
"""

# -------------------------------------------
# 3) PRIDOBITEV API KLJUČA (STREAMLIT SECRETS)
# -------------------------------------------
# Streamlit Cloud: ključ bo v st.secrets["GROQ_API_KEY"]
# Lokalno: lahko uporabiš okoljsko spremenljivko GROQ_API_KEY (ne .env na GitHub!)
api_key = None  # privzeto še nimamo ključa

if "GROQ_API_KEY" in st.secrets:  # v oblaku (Streamlit Secrets)
    api_key = st.secrets["GROQ_API_KEY"]  # preberemo ključ iz varnega shranjevanja
else:
    api_key = os.getenv("GROQ_API_KEY")  # lokalno iz okolja (npr. export/set)

if not api_key:  # če ključa ni, aplikacija ne more delati
    st.error("Manjka GROQ API ključ. Nastavi ga v Streamlit Secrets ali kot okoljsko spremenljivko.")
    st.stop()  # varno ustavimo aplikacijo

client = Groq(api_key=api_key)  # ustvarimo odjemalca za klice na Groq API

# -----------------------------------------
# 4) SPOMIN ZNOTRAJ SEJE (RESET OB REFRESH)
# -----------------------------------------
# Streamlit session_state se ponastavi, ko uporabnik osveži stran ali jo zapre.
# To izpolni zahtevo: spomin samo znotraj seje + reset po refresh/odhodu.

if "messages" not in st.session_state:  # če še ni zgodovine
    st.session_state.messages = []  # pripravimo prazen seznam sporočil

# UI gumb za ročni reset (ni nujen, ampak pomaga pri testiranju)
col1, col2 = st.columns([1, 1])  # razdelimo prostor na 2 stolpca
with col2:
    if st.button("🔄 Počisti pogovor"):  # če klikne
        st.session_state.messages = []  # pobrišemo zgodovino
        st.rerun()  # osvežimo prikaz

# --------------------------
# 5) PRIKAZ PRETEKLEGA CHAT-A
# --------------------------
for msg in st.session_state.messages:  # gremo čez vsa shranjena sporočila
    with st.chat_message(msg["role"]):  # role: "user" ali "assistant"
        st.markdown(msg["content"])  # izpišemo vsebino

# ---------------------------------
# 6) FUNKCIJA: KLIC LLM (GROQ)
# ---------------------------------
def generate_answer(user_text: str) -> str:
    """Pošlje pogovor na Groq LLM in vrne odgovor kot tekst (z varnim fallbackom)."""
    system_prompt = f"{DOMENA}\n\n{PRAVILA}"

    messages_for_model = [{"role": "system", "content": system_prompt}]
    for m in st.session_state.messages:
        messages_for_model.append({"role": m["role"], "content": m["content"]})

    # seznam modelov - če prvi ni na voljo, poskusi naslednjega
    candidate_models = [
        "llama-3.1-70b-versatile",
        "llama-3.1-8b-instant",
        "llama3-70b-8192",
        "llama3-8b-8192",
    ]

    last_error = None

    for model_name in candidate_models:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=messages_for_model,
                temperature=0.5,
                max_tokens=400,
            )
            return response.choices[0].message.content
        except Exception as e:
            last_error = e
            continue

    # če čisto vsi modeli padejo
    return (
        "Trenutno imam tehnične težave pri povezavi z jezikovnim modelom (API napaka). "
        "Poskusi prosim ponovno čez nekaj trenutkov."
    )

# ---------------------------------
# 7) VNOS UPORABNIKA (BREZ input())
# ---------------------------------
user_input = st.chat_input("Vpiši vprašanje...")  # Streamlit chat input

if user_input:  # če je uporabnik nekaj vpisal
    # 7.1 shranimo user sporočilo v spomin seje
    st.session_state.messages.append({"role": "user", "content": user_input})

    # 7.2 prikažemo user sporočilo
    with st.chat_message("user"):
        st.markdown(user_input)

    # 7.3 ustvarimo in prikažemo odgovor asistenta
    with st.chat_message("assistant"):
        with st.spinner("Razmišljam..."):  # lep UI indikator
            answer = generate_answer(user_input)  # klic LLM
            st.markdown(answer)  # prikažemo odgovor

    # 7.4 shranimo odgovor asistenta v spomin seje
    st.session_state.messages.append({"role": "assistant", "content": answer})