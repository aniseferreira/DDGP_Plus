#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import streamlit as st
from ddgp.morph import analyze_word
from ddgp.lexicon import lookup_lexicon, suggest_similar, get_lexicon
from ddgp.utils import normalize_unicode

# ------------------------------------------------------------
# Configuração da página
# ------------------------------------------------------------

st.set_page_config(
    page_title="DDGP Plus — Morfologia & Léxico",
    page_icon="📘",
    layout="centered",
)

st.title("📘 DDGP Plus — Analisador Morfológico & Léxico (3.x)")
st.write("Digite **uma palavra** (com ou sem diacríticos).")

# ------------------------------------------------------------
# Entrada do usuário
# ------------------------------------------------------------

user_input = st.text_input(
    "Palavra em grego antigo",
    value="",
    max_chars=100,
)

if user_input.strip():

    # Normalização Unicode
    norm = normalize_unicode(user_input.strip())

    st.subheader("🔤 Palavra normalizada")
    st.code(norm)

    # --------------------------------------------------------
    # MORFOLOGIA
    # --------------------------------------------------------
    st.subheader("🔎 Análise Morfológica")

    try:
        morph_data = analyze_word(norm)
        if morph_data:
            st.json(morph_data)
        else:
            st.info("Nenhuma análise morfológica encontrada.")
    except Exception as e:
        st.error(f"Erro na análise morfológica: {e}")

    # --------------------------------------------------------
    # LÉXICO
    # ------------------------------------
