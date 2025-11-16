# app.py — DDGP Plus (Morph Simple)
# -*- coding: utf-8 -*-

import streamlit as st
import json
import os
import unicodedata

# ==============================
#  Utils
# ==============================
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def normalize(text):
    return unicodedata.normalize("NFC", text or "").strip()

def simplify(text):
    return ''.join(ch for ch in unicodedata.normalize("NFD", text) if not unicodedata.combining(ch))


# ==============================
#  Paths
# ==============================
BASE_DIR = os.path.dirname(__file__)
DDGP_DATA = os.path.join(BASE_DIR, "ddgp", "data")

# índices DDGP
INDEX_FORMAS = load_json(os.path.join(DDGP_DATA, "ddgp_index_formas_final.json"))
INDEX_LEMAS  = load_json(os.path.join(DDGP_DATA, "ddgp_index_lemas.json"))
FORMA_TO_LEMA = load_json(os.path.join(DDGP_DATA, "ddgp_forma_to_lema.json"))

# dicionário completo
LEXICON = load_json(os.path.join(DDGP_DATA, "ddgp3x_entry.json"))

# morfologia simples
from ddgp.morph_simple import morph_analyze_simple


# ==============================
#   APP
# ==============================
st.title("📘 DDGP Plus — Analisador Morfológico (versão simples)")

palavra = st.text_input("Digite uma forma grega:", "")

if palavra:
    st.subheader("🧩 Análise morfológica")

    resultado = morph_analyze_simple(palavra)
    st.json(resultado)

    # ------------------------------------------------
    # 1) Procurar lema via forma → lema direto
    # ------------------------------------------------
    forma_s = simplify(palavra)

    lema = None

    if forma_s in FORMA_TO_LEMA:
        lema = FORMA_TO_LEMA[forma_s]
    else:
        # ------------------------------------------------
        # 2) Usar lema da morfologia simples
        # ------------------------------------------------
        lema = resultado.get("lema")

    # Se ainda não houver lema, parar
    if not lema:
        st.warning("A análise não retornou um lema e não há correspondência no índice.")
        st.stop()

    # Normalizar lema
    lema_norm = simplify(lema)


    # ==============================
    #  Busca no dicionário DDGP
    # ==============================
    st.subheader("📖 Verbete no DDGP")

    if lema_norm in INDEX_LEMAS:
        entry_id = INDEX_LEMAS[lema_norm]

        entry = LEXICON.get(str(entry_id))
        if entry:
            st.markdown(f"### **{entry['gword']}**")
            st.write(entry["pdesc"])
        else:
            st.error("ID encontrado no índice, mas verbete não localizado no dicionário JSON.")
    else:
        st.warning("Nenhum verbete encontrado no DDGP para este lema.")
