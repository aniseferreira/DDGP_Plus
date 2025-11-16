import streamlit as st
import json
import os

# --------------------------------------------------------------------
# Importa MORPH SIMPLES
# --------------------------------------------------------------------
from ddgp.morph_simple import morph_analyze_simple

# --------------------------------------------------------------------
# Carrega DDGP (ddgp3x_entry.json) da pasta /ddgp/data/
# --------------------------------------------------------------------
BASE_DIR = os.path.dirname(__file__)
DDGP_PATH = os.path.join(BASE_DIR, "ddgp", "data", "ddgp3x_entry.json")

def load_ddgp():
    try:
        with open(DDGP_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return None

DDGP = load_ddgp()

# Indexa lemas → entrada completa
DDGP_INDEX = {}
if DDGP:
    for item in DDGP:
        # lema = gword até vírgula ou espaço
        lemma_raw = item.get("gword","").split(",")[0].strip()
        DDGP_INDEX[lemma_raw] = item

# --------------------------------------------------------------------
# Lookup no DDGP
# --------------------------------------------------------------------
def lookup_lema(lema):
    if not lema:
        return None

    lema_simpl = lema.replace("́","").replace("̀","")
    for k,v in DDGP_INDEX.items():
        if k == lema or k == lema_simpl:
            return v

    return None

# --------------------------------------------------------------------
# Interface
# --------------------------------------------------------------------
st.title("📘 DDGP Plus — Morfologia + Dicionário (versão simples)")

palavra = st.text_input("Digite uma forma grega politônica ou sem diacríticos.")

if palavra:
    st.subheader("🧩 Análise morfológica")
    resultado = morph_analyze_simple(palavra)
    st.json(resultado)

    lema = resultado.get("lema")

    st.subheader("📗 Dicionário DDGP (lema)")
    info = lookup_lema(lema)

    if info:
        st.json(info)
    else:
        st.info("Nenhuma entrada do DDGP encontrada para este lema.")


