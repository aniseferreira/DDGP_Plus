import streamlit as st
import json
import os
import unicodedata

from ddgp.morph_v3 import analyze


BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "ddgp", "data")


def load_json(fname):
    path = os.path.join(DATA_DIR, fname)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# === DDGP DATA ===
INDEX_FORMAS = load_json("ddgp_forma_to_lema.json")
INDEX_LEMAS = load_json("ddgp_index_lemas.json")
LEXICON = load_json("ddgp3x_entry.json")


def simplify(text):
    """Remove diacríticos e normaliza."""
    return ''.join(
        ch for ch in unicodedata.normalize("NFD", text)
        if not unicodedata.combining(ch)
    ).lower()


# ================================
#     INTERFACE STREAMLIT
# ================================

st.title("DDGP Plus — Morph V3")


word = st.text_input("Digite uma forma grega:", "")

if word:

    st.subheader("🧩 Morph V3 — Análise morfológica")

    res = analyze(word)
    st.json(res)

    # Melhor candidato (V3 escolhe automaticamente)
    best = res.get("best")
    if not best:
        st.warning("Nenhuma análise morfológica encontrada.")
        st.stop()

    lemma = best.get("lemma")
    if not lemma:
        st.warning("A análise morfológica não retornou lema.")
        st.stop()

    st.subheader("📘 Dicionário DDGP")

    simple_input = simplify(word)
    simple_lemma = simplify(lemma)

    # -------------------------------
    # 1) PRIMEIRO, LOOKUP POR FORMA
    # -------------------------------
    if simple_input in INDEX_FORMAS:
        entry_id = INDEX_FORMAS[simple_input]
        entry = LEXICON.get(str(entry_id))
        if entry:
            st.markdown(f"### **{entry['gword']}**")
            st.write(entry["pdesc"])
            st.stop()

    # ---------------------------------
    # 2) SEGUNDO, LOOKUP POR LEMA
    # ---------------------------------
    if simple_lemma in INDEX_LEMAS:
        entry_id = INDEX_LEMAS[simple_lemma]
        entry = LEXICON.get(str(entry_id))
        if entry:
            st.markdown(f"### **{entry['gword']}**")
            st.write(entry["pdesc"])
        else:
            st.error("ID encontrado, mas entrada não está no ddgp3x_entry.json.")
    else:
        st.warning("Nenhum verbete encontrado para forma nem para o lema.")
