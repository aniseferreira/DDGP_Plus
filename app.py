# app.py — versão FINAL para Morph Simple
import streamlit as st
from ddgp.morph_simple import morph_analyze_simple
from ddgp.ddgp_lookup import buscar_lema_no_ddgp   # se já existe no seu projeto

st.set_page_config(page_title="DDGP Plus — Morfologia", layout="centered")

st.title("📘 DDGP Plus — Analisador Morfológico (versão simples)")
palavra = st.text_input("Digite uma forma grega:")

if palavra:
    st.subheader("🧩 Análise morfológica")

    resultado = morph_analyze_simple(palavra)
    st.json(resultado)

    # -----------------------
    # CONSULTA AO DDGP
    # -----------------------
    lema = resultado.get("lema")

    st.subheader("📚 Dicionário DDGP")

    if lema:
        dados = buscar_lema_no_ddgp(lema)
        if dados:
            st.json(dados)
        else:
            st.error("Nenhum verbete encontrado para este lema.")
    else:
        st.warning("Nenhum lema identificado pela morfologia.")
