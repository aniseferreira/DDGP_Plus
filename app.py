# app.py — DDGP Plus (versão simples + dicionário) — com logo, favicon e rodapé seguro
# -*- coding: utf-8 -*-

import os
import json
import unicodedata
import streamlit as st

# configure page (title + favicon)
LOGO_URL = "https://raw.githubusercontent.com/aniseferreira/DDGP_Plus/main/ddgp/logo.png"  
# original logo URL
# If you prefer a local logo, put it in ddgp/static/ddgp.png and set LOGO_LOCAL = "ddgp/static/ddgp.png"
LOGO_LOCAL = None

st.set_page_config(page_title="DDGP Plus — Morph & Dictionary", page_icon=LOGO_URL, layout="wide")

# helper utils
def normalize(text):
    return unicodedata.normalize("NFC", (text or "")).strip()

def simplify(text):
    s = normalize(text)
    return "".join(ch for ch in unicodedata.normalize("NFD", s) if not unicodedata.combining(ch)).lower()

# safe json loader
def load_json_safe(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except Exception as e:
        st.warning(f"Erro ao ler JSON {os.path.basename(path)}: {e}")
        return None

# try to import morph_simple (placed in ddgp/morph_simple.py)
MORPH_AVAILABLE = False
try:
    from ddgp.morph_simple import morph_analyze_simple
    MORPH_AVAILABLE = True
except Exception as e:
    morph_analyze_simple = None
    st.warning("morph_simple não pôde ser importado — a análise morfológica ficará indisponível. Erro: " + str(e))

# Load DDGP JSONs (if present)
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "ddgp", "data")

DDGP_ENTRY = load_json_safe(os.path.join(DATA_DIR, "ddgp3x_entry.json")) or {}
DDGP_INDEX_LEMAS = load_json_safe(os.path.join(DATA_DIR, "ddgp_index_lemas.json")) or {}
DDGP_INDEX_FORMAS = load_json_safe(os.path.join(DATA_DIR, "ddgp_index_formas_final.json")) or {}
DDGP_FORMA_TO_LEMA = load_json_safe(os.path.join(DATA_DIR, "ddgp_forma_to_lema.json")) or {}

# --- HEADER with logo on the left ---
col_left, col_title = st.columns([1, 10])
with col_left:
    try:
        if LOGO_LOCAL and os.path.exists(os.path.join(BASE_DIR, LOGO_LOCAL)):
            st.image(os.path.join(BASE_DIR, LOGO_LOCAL), width=64)
        else:
            st.image(LOGO_URL, width=64)
    except Exception:
        # fallback: show nothing (não quebrar)
        st.text("")

with col_title:
    st.markdown("## DDGP Plus — Analisador Morfológico e Dicionário Digital de Grego–Português")
    st.markdown("Versão 2025 — online")

st.markdown("---")

# Input
st.write("Digite uma forma grega (com ou sem diacríticos).")
palavra = st.text_input("Forma grega politônica ou sem diacríticos", value="")

if palavra:
    st.subheader("🧩 Resultado")

    # 1) Try exact form lookup in ddgp_index_formas (fast path)
    simp_form = simplify(palavra)
    found_entries = []
    if DDGP_INDEX_FORMAS and simp_form in DDGP_INDEX_FORMAS:
        ids = DDGP_INDEX_FORMAS[simp_form]
        # collect first up to 10 entries
        for i in ids[:10]:
            ent = DDGP_ENTRY.get(str(i))
            if ent:
                found_entries.append(ent)

    # 2) Try forma->lema index fallback
    lema_from_form = None
    if not found_entries and DDGP_FORMA_TO_LEMA and simp_form in DDGP_FORMA_TO_LEMA:
        lema_from_form = DDGP_FORMA_TO_LEMA[simp_form]

    # 3) If morph available, analyze and try to get lemma
    morph_result = None
    if MORPH_AVAILABLE:
        try:
            morph_result = morph_analyze_simple(palavra)
        except Exception as e:
            st.error(f"Erro na análise morfológica: {e}")
            morph_result = None

    # Show morph result
    if morph_result:
        st.markdown("**Análise morfológica (simples)**")
        st.json(morph_result)
    else:
        st.info("Análise morfológica não disponível.")

    # If we have a lemma candidate from morph or from forma_to_lema, try to lookup dictionary
    lemma_candidates = []
    if morph_result and morph_result.get("lema"):
        lemma_candidates.append(simplify(morph_result.get("lema")))
    if lema_from_form:
        lemma_candidates.append(simplify(lema_from_form))
    # remove duplicates keeping order
    seen = set(); lemma_candidates = [x for x in lemma_candidates if not (x in seen or seen.add(x))]

    # If dictionary entries were found by exact form, show them first
    if found_entries:
        st.subheader("📘 Entradas do DDGP (lookup por forma)")
        for ent in found_entries:
            gid = ent.get("id","?")
            gword = ent.get("gword","")
            pdesc = ent.get("pdesc","")
            st.markdown(f"**{gword}** (id: {gid})")
            st.write(pdesc)
    elif lemma_candidates:
        st.subheader("📘 Lookup por lema candidato")
        matched_any = False
        for cand in lemma_candidates:
            if cand in DDGP_INDEX_LEMAS:
                matched_any = True
                entry_id = DDGP_INDEX_LEMAS[cand]
                ent = DDGP_ENTRY.get(str(entry_id))
                if ent:
                    st.markdown(f"**{ent.get('gword','')}** (id: {entry_id})")
                    st.write(ent.get("pdesc",""))
                else:
                    st.warning(f"Lema '{cand}' encontrado no índice (id {entry_id}), mas entrada ausente no JSON ddgp3x_entry.json.")
            else:
                st.info(f"Nenhuma entrada encontrada no índice para o lema candidato: **{cand}**")
        if not matched_any:
            st.warning("Nenhuma entrada do DDGP encontrada para a(s) forma(s) ou lema(s) candidatos.")
    else:
        st.warning("Nenhuma entrada do DDGP encontrada para esta forma ou lema.")

# --- FOOTER (rodapé minimal, versátil e estável) ---
# Two versions: compact (shown) and long (in expandable)
footer_short = """
**DDGP Plus** — Analisador Morfológico e Dicionário Digital de Grego–Português.  
Versão 2025. Disponível em: https://ddgp-plus.streamlit.app  
Baseado no Dicionário Digital de Grego-Português (DDGP e DGP), Projeto Letras Clássicas Digitais /UNESP.  
Licenciado sob **CC BY–NC–ND 4.0**.
"""

footer_long = """
**Créditos e licença (detalhado)**

- Base: Dicionário Digital de Grego–Português (DDGP), Projeto Letras Clássicas Digitais — UNESP.  
- Licença do conteúdo digital: CC BY–NC–ND 4.0.  
- Créditos aos autores da versão impressa, coordenadores e instituições conforme rodapé em hipatia.fclar.unesp.br.  
- Desenvolvimento do front-end e integração: equipe de desenvolvimento (registro técnico disponível sob solicitação).
"""

# place footer in a container so HTML injection is minimal (no custom CSS)
st.markdown("---")
st.markdown(footer_short)
with st.expander("Créditos e licença (detalhado)"):
    st.markdown(footer_long)

# small copyright note aligned right
st.markdown("<div style='text-align:right; font-size:0.85em; color:gray;'>© Projeto DDGP — UNESP (digital). CC BY–NC–ND 4.0</div>", unsafe_allow_html=True)
