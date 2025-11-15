#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import streamlit as st
from ddgp.morph import analyze_word
from ddgp.lexicon import lookup_lexicon
from ddgp.utils import normalize_unicode

# ------------------------------------------------------------
# Configuração geral da página
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
    # Normalização (NFC por padrão)
    norm = normalize_unicode(user_input.strip())

    st.subheader("🔤 Palavra normalizada")
    st.code(norm)

    # --------------------------------------------------------
    # 1. Análise Morfológica (módulo ddgp/morph.py)
    # --
