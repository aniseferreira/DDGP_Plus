# app.py — DDGP Plus (versão simples)
# Funciona exclusivamente com morph_simple.py
# Não chama ddgp_lookup nem nenhum outro módulo

import streamlit as st
from ddgp.morph_simple import morph_analyze_simple

st.set_page_config(page_title="DDGP Plus — Morfologia Simples", layout="centered")

st.title("📘 DDGP Plus — Analisador Morfológico (versão simples)")
st.write("Digite uma forma grega politônica ou sem diacríticos.")

palavra = st.text_input("Forma grega:", "")

if palavra:
    st.subheader("🧩 Análise morfológica")
    try:
        resultado = morph_analyze_simple(palavra)
        st.json(resultado)
    except Exception as e:
        st.error("Erro interno na análise morfológica.")
        st.code(str(e))

