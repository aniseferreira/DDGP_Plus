# app.py — DDGP Plus (base 27/11/25 + WIC)
# -*- coding: utf-8 -*-

import os
import json
import unicodedata
import re
from pathlib import Path
import streamlit as st

from ddgp.translit import transliterate_to_greek
from ddgp.formatting import format_pdesc

# ============================================================
# DOWNLOAD DO MODELO UD (uma vez por ambiente)
# ============================================================

try:
    import stanza
    stanza.download("grc", processors="tokenize,pos,lemma,morph", verbose=False)
except Exception:
    pass

# ============================================================
# MORPH_RAW (UD) — PIPELINE
# ============================================================

UD_AVAILABLE = False
ud_nlp = None

try:
    import stanza
    ud_nlp = stanza.Pipeline(
        lang="grc",
        package="proiel",   # ou agdt, conforme o que você usou
        processors="tokenize, pos,lemma,morph",
        tokenize_no_ssplit=True,
        use_gpu=False
    )
    UD_AVAILABLE = True
except Exception as e:
    UD_AVAILABLE = False

def morph_ud_analyze(sentence: str):
    if not UD_AVAILABLE or not ud_nlp:
        return None

    doc = ud_nlp(sentence)
    results = []

    for sent in doc.sentences:
        for word in sent.words:
            results.append({
                "token": word.text,
                "lema": word.lemma,
                "upos": word.upos,
                "feats": word.feats
            })

    return results



# ============================================================
# CONFIGURAÇÃO DA PÁGINA / LOGO / CSS  (LEGADO — PRESERVADO)
# ============================================================

LOGO_URL = "https://raw.githubusercontent.com/aniseferreira/DDGP_Plus/main/ddgp/logo.png"
LOGO_LOCAL = None

st.set_page_config(
    page_title="DDGP Plus — Morph & Dictionary",
    page_icon=LOGO_URL,
    layout="wide"
)

def load_css(file_name: str):
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass

for css in [
    "ddgp/style/style.css",
    "ddgp/style/style_map.css",
    "style.css",
    "style_map.css",
]:
    if Path(css).exists():
        load_css(css)

# ============================================================
# UTILITÁRIOS UNICODE / JSON  (LEGADO)
# ============================================================

def normalize(text):
    return unicodedata.normalize("NFC", (text or "")).strip()

def simplify(text):
    s = normalize(text)
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = "".join(ch for ch in s if not ch.isdigit())
    s = s.replace(".", "").replace("-", "").replace("/", "").replace(" ", "")
    return s.lower()

def load_json_safe(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

# ============================================================
# CARREGAR DADOS DDGP  (LEGADO)
# ============================================================

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "ddgp", "data")

DDGP_ENTRY = load_json_safe(os.path.join(DATA_DIR, "ddgp3x_entry.json"))
DDGP_INDEX_LEMAS = load_json_safe(os.path.join(DATA_DIR, "ddgp_index_lemas.json"))
DDGP_INDEX_FORMAS = load_json_safe(os.path.join(DATA_DIR, "ddgp_index_formas_final.json"))
DDGP_FORMA_TO_LEMA = load_json_safe(os.path.join(DATA_DIR, "ddgp_forma_to_lema.json"))

# ============================================================
# HEADER / LOGO  (LEGADO)
# ============================================================

col_left, col_title = st.columns([1, 10])
with col_left:
    try:
        st.image(LOGO_URL, width=120)
    except Exception:
        pass

with col_title:
    st.markdown("## DDGP Plus — Analisador Morfológico e Dicionário Digital de Grego–Português")
    st.markdown("Versão 2025-2026 — online")

st.markdown("---")

# ============================================================
# WIC — ANÁLISE MORFOLÓGICA EM CONTEXTO (UD)
# ============================================================

st.markdown("### 🧩 Análise morfológica em contexto (WIC — UD)")

wic_sentence = st.text_input(
    "Cole uma frase curta contendo o vocábulo:",
    placeholder="ex.: τὸ προκείμενον ἵνα μὴ μεῖζον ἡμῖν"
)

if wic_sentence:
    if not UD_AVAILABLE:
        st.error(
            "A análise morfológica em contexto (UD) não está disponível neste ambiente de hospedagem." 
            "Em servidores com mais memória, o recurso é ativado automaticamente."
            "O DDGP continua funcionando normalmente."
        )
    else:
        ud_result = morph_ud_analyze(wic_sentence)

        if not ud_result:
            st.warning("Não foi possível analisar a frase com o pipeline UD.")
        else:
            st.subheader("Resultado morfológico (UD)")

            for i, tok in enumerate(ud_result):
                cols = st.columns([2, 2, 2, 3, 2])

                cols[0].markdown(f"**{tok['token']}**")
                cols[1].markdown(tok["lema"] or "—")
                cols[2].markdown(tok["upos"] or "—")
                cols[3].markdown(tok["feats"] or "—")

                if tok["lema"]:
                    if cols[4].button(
                        "🔎 DDGP",
                        key=f"ddgp_ud_{i}"
                    ):
                        st.session_state["campo_ascii"] = tok["lema"]

st.markdown("---")


# ============================================================
# INPUT INTELIGENTE DDGP  (LEGADO — PRESERVADO)
# ============================================================

palavra = (
    st.session_state.get("campo_grc")
    or st.session_state.get("campo_ascii")
    or ""
).strip()


# Instrução (MANTIDA)
st.markdown(
    '<div id="ddgp-instrucao">'
    'Digite (pode usar letras latinas: legw, ferw, akouw — ou grego diretamente sem diacríticos):'
    '</div>',
    unsafe_allow_html=True
)

# Campo de input visível (SEM on_change)
txt_raw = st.text_input(
    " ",
    key="campo_ascii"
)

# NORMALIZAÇÃO DIRETA (SEM EVENTO)
if txt_raw:
    # ASCII → grego
    if all(ord(ch) < 128 for ch in txt_raw):
        palavra = transliterate_to_greek(txt_raw.lower())
    else:
        palavra = txt_raw
else:
    palavra = ""


# ============================================================
# FUNÇÕES DE LOOKUP DDGP  (LEGADO)
# ============================================================

def find_entry_ids_for_lemma_candidate(cand: str):
    if not cand:
        return []
    base = simplify(cand)
    results = []
    seen = set()

    if base in DDGP_INDEX_LEMAS:
        eid = DDGP_INDEX_LEMAS[base]
        results.append(eid); seen.add(eid)

    for k, eid in DDGP_INDEX_LEMAS.items():
        k_s = simplify(k)
        if k_s.startswith(base) and eid not in seen:
            results.append(eid); seen.add(eid)

    return results

# ============================================================
# MAIN — CONSULTA DDGP  (LEGADO)
# ============================================================

if palavra:
    st.subheader("📘 Resultados do DDGP")

    simp_form = simplify(palavra)
    found_entries = []

    if simp_form in DDGP_INDEX_FORMAS:
        for i in DDGP_INDEX_FORMAS[simp_form][:10]:
            ent = DDGP_ENTRY.get(str(i))
            if ent:
                found_entries.append(ent)

    if found_entries:
        for ent in found_entries:
            st.markdown(f"**{ent.get('gword','')}** (id: {ent.get('id','?')})")
            st.markdown(format_pdesc(ent.get("pdesc","")), unsafe_allow_html=True)
    else:
        lemma_candidates = []
        if simp_form in DDGP_FORMA_TO_LEMA:
            lemma_candidates.append(DDGP_FORMA_TO_LEMA[simp_form])

        shown = False
        for cand in lemma_candidates:
            for eid in find_entry_ids_for_lemma_candidate(cand):
                ent = DDGP_ENTRY.get(str(eid))
                if ent:
                    shown = True
                    st.markdown(f"**{ent.get('gword','')}** (id: {eid})")
                    st.markdown(format_pdesc(ent.get("pdesc","")), unsafe_allow_html=True)

        if not shown:
            st.warning("Nenhuma entrada do DDGP encontrada para esta forma.")

        # --- Fallback FINAL: tratar a forma como lema direto ---
        if not shown:
            entry_ids = find_entry_ids_for_lemma_candidate(simp_form)
            for eid in entry_ids:
                ent = DDGP_ENTRY.get(str(eid))
                if ent:
                    shown = True
                    st.markdown(f"**{ent.get('gword','')}** (id: {eid})")
                    st.markdown(format_pdesc(ent.get("pdesc","")), unsafe_allow_html=True)


# ============================================================
# FOOTER  (LEGADO)
# ============================================================

# --- FOOTER ---
st.markdown("---")
footer_short = """
**DDGP Plus** — Analisador Morfológico e Dicionário Digital de Grego–Português.  
Versão 2025. Disponível em: https://ddgp-plus-morpho.streamlit.app/  
Baseado no Dicionário Digital de Grego–Português (DDGP e DGP), pelo Projeto Letras Clássicas Digitais FCLAr/UNESP .
Licenciado sob **CC BY–NC–ND 4.0**.
"""
footer_long = """
**Créditos e licença (detalhado)**

- Base: Dicionário Digital de Grego–Português (DDGP e DGP), Projeto Letras Clássicas Digitais — FCLAr/UNESP.  
- Responsável: Anise D'Orange Ferreira.
- Licença do conteúdo digital: CC BY–NC–ND 4.0.  
- Créditos aos autores da versão impressa do DGP, coordenadores e instituições conforme rodapé em http://hipatia.fclar.unesp.br.  
- Desenvolvimento do front-end e integração: equipe de desenvolvimento (registro técnico disponível sob solicitação).
"""
st.markdown(footer_short)
with st.expander("Créditos e licença (detalhado)"):
    st.markdown(footer_long)
st.markdown("<div style='text-align:right; font-size:0.85em; color:gray;'>© Projeto DDGP — UNESP (digital). CC BY–NC–ND 4.0</div>", unsafe_allow_html=True)
