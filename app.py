# app.py — DDGP Plus (Morph V3)

import streamlit as st
import json
import os
import unicodedata

from ddgp.morph_v3 import analyze


BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "ddgp", "data")

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

INDEX_FORMAS = load_json(os.path.join(DATA_DIR, "ddgp_index_formas_final.json"))
INDEX_LEMAS = load_json(os.path.join(DATA_DIR, "ddgp_index_lemas.json"))
LEXICON = load_json(os.path.join(DATA_DIR, "ddgp3x_entry.json"))

def simplify(text):
    return ''.join(ch for ch in unicodedata.normalize("NFD", text) if not unicodedata.combining(ch))

def main():
    st.title("DDGP Plus — Morph V3")

    word = st.text_input("Digite uma forma grega:", "")

    if word:
        st.subheader("🧩 Morph V3 — Análise morfológica")
        res = analyze(word)
        st.json(res)

        # Lema reconstruído
        best = res.get("best")
        if not best:
            st.warning("Nenhuma análise morfológica encontrada.")
            return

        lemma = best.get("lemma")
        if not lemma:
            st.warning("A análise morfológica não retornou lemma.")
            return

        st.subheader("📘 Dicionário DDGP")

        lemma_s = simplify(lemma)

        if lemma_s in INDEX_LEMAS:
            entry_id = INDEX_LEMAS[lemma_s]
            entry = LEXICON.get(str(entry_id))
            if entry:
                st.markdown(f"### {entry['gword']}")
                st.write(entry["pdesc"])
            else:
                st.error("ID encontrado no índice, mas não existe no dicionário JSON.")
        else:
            st.warning("Nenhuma entrada do DDGP corresponde a este lema.")

if __name__ == "__main__":
    main()
