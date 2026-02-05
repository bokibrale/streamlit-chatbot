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
st.caption("Odgovarjam izključno v slovenščini in samo o vsebini spletne strani »Pametna tehnologija v vsakdanjem življenju«.")

# ------------------------------------------------------
# 2) SPECIALIZACIJA (VEZANA NA TVOJO GOOGLE SITES STRAN)
# ------------------------------------------------------
DOMENA = """
Sem specializiran chatbot za spletno stran "Pametna tehnologija v vsakdanjem življenju".
Odgovarjam samo na vprašanja, ki so neposredno povezana z vsebino te strani.

Na strani so predstavljene teme:
1) Domov:
- kaj je pametna tehnologija v vsakdanjem življenju,
- primeri uporabe (pametni telefoni, domovi, avtomobili, splet),
- koristi (udobje, varnost, učinkovitost).

2) Umetna inteligenca:
- kaj je umetna inteligenca (AI),
- primeri uporabe (navigacija, priporočila, prepoznavanje govora, chatboti),
- razlaga pojma chatbot.

3) Pametni dom:
- kaj je pametni dom in kako deluje (povezane naprave, avtomatizacija, nadzor na daljavo),
- upravljanje s telefonom ali glasovnim asistentom,
- primeri pametnih naprav (žarnice, termostati, varnostne kamere, vtičnice, glasovni pomočniki).

Če uporabnik vpraša nekaj, kar ni povezano z zgornjimi temami, moram vprašanje vljudno zavrniti.
"""

PRAVILA = """
Pravila odgovarjanja:
1) Odgovarjaj izključno v slovenščini.
2) Odgovarjaj samo o vsebini spletne strani "Pametna tehnologija v vsakdanjem življenju"
   (Domov / Umetna inteligenca / Pametni dom).
3) Če vprašanje ni povezano s temi temami, vljudno zavrni, npr.:
   "Za to področje nimam informacij, ker sem namenjen razlagi pametne tehnologije, AI in pametnega doma."
4) Odgovori naj bodo kratki, pregledni in slovnično pravilni.
5) Uporabi alineje, kadar naštevaš primere ali korake.
6) Ne izmišljaj si dodatnih dejstev, ki niso na strani; ostani pri razlagi pojmov in primerih iz vsebine.
"""

# ------------------------------------------------------
# 2.1) HARD FILTER: ČE NI V DOMENI, NE KLIČI API-ja
# ------------------------------------------------------
def is_in_domain(text: str) -> bool:
    t = (text or "").lower()

    keywords = [
        # splošno
        "pametna tehnologija", "pametni telefon", "pametni telefoni", "udobje", "varnost", "učinkovitost",
        "tehnologija", "vsakdan", "vsakdanje življenje", "digitalno",

        # AI
        "umetna inteligenca", "ai", "chatbot", "klepetalnik", "prepoznavanje govora",
        "navigacija", "priporočila", "priporočilni", "algoritem", "priporočilni algoritem",

        # pametni dom
        "pametni dom", "smart home", "avtomatizacija", "nadzor na daljavo", "glasovni asistent",
        "pametne žarnice", "žarnice", "termostat", "varnostne kamere", "kamera",
        "pametne vtičnice", "vtičnice", "glasovni pomočniki", "povezane naprave",
    ]

    return any(k in t for k in keywords)

# -------------------------------------------
# 3) PRIDOBITEV API KLJUČA (STREAMLIT SECRETS)
# -------------------------------------------
api_key = None  # privzeto še nimamo ključa

# Streamlit včasih lokalno vrže napako že ob branju st.secrets, zato uporabimo try/except
try:
    api_key = st.secrets.get("GROQ_API_KEY")
except Exception:
    api_key = None

# Lokalno fallback na env
if not api_key:
    api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    st.error("Manjka GROQ API ključ. Nastavi ga v Streamlit Secrets ali kot okoljsko spremenljivko.")
    st.stop()

client = Groq(api_key=api_key)

# -----------------------------------------
# 4) SPOMIN ZNOTRAJ SEJE (RESET OB REFRESH)
# -----------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

col1, col2 = st.columns([1, 1])
with col2:
    if st.button("🔄 Počisti pogovor"):
        st.session_state.messages = []
        st.rerun()

# --------------------------
# 5) PRIKAZ PRETEKLEGA CHAT-A
# --------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------------------------
# 6) FUNKCIJA: KLIC LLM (GROQ)
# ---------------------------------
def generate_answer(user_text: str) -> str:
    """Pošlje pogovor na Groq LLM in vrne odgovor kot tekst (z varnim fallbackom)."""
    system_prompt = f"{DOMENA}\n\n{PRAVILA}"

    messages_for_model = [{"role": "system", "content": system_prompt}]
    for m in st.session_state.messages:
        messages_for_model.append({"role": m["role"], "content": m["content"]})

    candidate_models = [
        "llama-3.1-70b-versatile",
        "llama-3.1-8b-instant",
        "llama3-70b-8192",
        "llama3-8b-8192",
    ]

    for model_name in candidate_models:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=messages_for_model,
                temperature=0.5,
                max_tokens=400,
            )
            return response.choices[0].message.content
        except Exception:
            continue

    return (
        "Trenutno imam tehnične težave pri povezavi z jezikovnim modelom (API napaka). "
        "Poskusi prosim ponovno čez nekaj trenutkov."
    )

# ---------------------------------
# 7) VNOS UPORABNIKA (BREZ input())
# ---------------------------------
user_input = st.chat_input("Vpiši vprašanje...")

if user_input:
    # 7.1 shranimo user sporočilo v spomin seje
    st.session_state.messages.append({"role": "user", "content": user_input})

    # 7.2 prikažemo user sporočilo
    with st.chat_message("user"):
        st.markdown(user_input)

    # 7.3 odgovor
    with st.chat_message("assistant"):
        with st.spinner("Razmišljam..."):
            # HARD FILTER: izven domene -> takojšnja zavrnitev (brez API klica)
            if not is_in_domain(user_input):
                answer = (
                    "Za to vprašanje nimam informacij, ker sem namenjen samo razlagi vsebine strani "
                    "»Pametna tehnologija v vsakdanjem življenju« (pametna tehnologija, umetna inteligenca, pametni dom). "
                    "Lahko vprašaš npr. kaj je pametni dom, kaj je umetna inteligenca ali kaj je chatbot."
                )
            else:
                answer = generate_answer(user_input)

            st.markdown(answer)

    # 7.4 shranimo odgovor asistenta v spomin seje
    st.session_state.messages.append({"role": "assistant", "content": answer})
