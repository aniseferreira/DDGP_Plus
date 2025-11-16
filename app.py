# -*- coding: utf-8 -*-
import streamlit as st
from ddgp.lexicon import search
from ddgp.morph import morph_analyze   # módulo morfológico simples

st.set_page_config(
    page_title="DDGP Plus",
    page_icon="📚",
    layout="centered"
)

st.title("📚 DDGP Plus — Analisador Morfológico & Léxico")

st.write(
    """
    Digite qualquer forma grega (com ou sem diacríticos).
    O sistema faz:
    - normalização
    - análise morfológica
    - identificação do lema
    - busca no dicionário DDGP 3.x
    """
)

# --------------------------------------------------------------------
# Caixinha de input do usuário
# --------------------------------------------------------------------
term = st.text_input("Forma grega:", "")

if st.button("Analisar"):
    if not term.strip():
        st.warning("Digite uma forma grega.")
    else:
        st.header("🔍 Resultado")

        # ---------------------------------------------------------------
        # 1. MORFOLOGIA
        # ---------------------------------------------------------------
        morph = morph_analyze(term)

        st.subheader("🧩 Análise morfológica")
        st.json(morph)

        lemma = morph.get("lemma")

        # Se o módulo não achar, ainda tentamos o lexicon diretamente
        if not lemma:
            st.warning("Morfologia não identificou o lema. Tentando lookup direto no dicionário...")
            result = search(term)
        else:
            # -----------------------------------------------------------
            # 2. LEXICON: busca o lema no DDGP
            # -----------------------------------------------------------
            result = search(lemma)

        st.subheader("📘 Dicionário DDGP")

        if not result or not result.get("lemma_id"):
            st.error("Nenhuma entrada do DDGP encontrada para esta forma ou para o lema.")
        else:
            lemma_id = result["lemma_id"]
            entry = result["lemma_entry"]

            st.markdown(f"### **Lema:** {entry['gword']}  \n**ID:** {lemma_id}")
            st.markdown(f"**Descrição:**\n\n{entry['pdesc']}")

            # -----------------------------------------------------------
            # 3. Formas relacionadas (do mesmo lema)
            # -----------------------------------------------------------
            st.subheader("🔗 Formas relacionadas")
            forms = result.get("form_entries", [])

            if not forms:
                st.write("Nenhuma forma alternativa registrada.")
            else:
                for f in forms:
                    st.markdown(f"**{f['gword']}** — ID {f['id']}")


# --------------------------------------------------------------------
# Rodapé
# --------------------------------------------------------------------
st.markdown("---")
st.caption("DDGP Plus — Projeto lexical-morfológico para Grego Antigo • 2025")
