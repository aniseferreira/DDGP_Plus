# app.py — DDGP Plus (corrigido)
# -*- coding: utf-8 -*-

import os
import json
import unicodedata
import re
from pathlib import Path
import streamlit as st

# configure page (title + favicon)
LOGO_URL = "https://raw.githubusercontent.com/aniseferreira/DDGP_Plus/main/ddgp/logo.png"
LOGO_LOCAL = None
st.set_page_config(page_title="DDGP Plus — Morph & Dictionary", page_icon=LOGO_URL, layout="wide")

# ---------------------------
# Carregar CSS customizado
# ---------------------------
def load_css(file_name: str):
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            css = f"<style>{f.read()}</style>"
            st.markdown(css, unsafe_allow_html=True)
    except FileNotFoundError:
        pass

style_main = "ddgp/style/style.css"
style_map = "ddgp/style/style_map.css"
if Path(style_main).exists():
    load_css(style_main)
if Path(style_map).exists():
    load_css(style_map)
if Path("style.css").exists():
    load_css("style.css")
if Path("style_map.css").exists():
    load_css("style_map.css")

# ---------------------------
# Utilitários Unicode e JSON
# ---------------------------
def normalize(text):
    return unicodedata.normalize("NFC", (text or "")).strip()

def simplify(text):
    s = normalize(text)
    # remove combining diacritics
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    # remove digits and basic punctuation used in lemmata (retain greek letters and ascii)
    s = "".join(ch for ch in s if not ch.isdigit())
    s = s.replace(".", "").replace("-", "").replace("/", "").replace(" ", "")
    return s.lower()

def load_json_safe(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except Exception as e:
        st.warning(f"Erro ao ler JSON {os.path.basename(path)}: {e}")
        return None

# ---------------------------
# Carregar dados DDGP e abreviaturas
# ---------------------------
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "ddgp", "data")

DDGP_ENTRY = load_json_safe(os.path.join(DATA_DIR, "ddgp3x_entry.json")) or {}
DDGP_INDEX_LEMAS = load_json_safe(os.path.join(DATA_DIR, "ddgp_index_lemas.json")) or {}
DDGP_INDEX_FORMAS = load_json_safe(os.path.join(DATA_DIR, "ddgp_index_formas_final.json")) or {}
DDGP_FORMA_TO_LEMA = load_json_safe(os.path.join(DATA_DIR, "ddgp_forma_to_lema.json")) or {}

ABREV_PATHS = [os.path.join(DATA_DIR, "abrev.json"), "ddgp/abrev.json", "abrev.json", "/mnt/data/abrev.json"]
ABREV = {}
for p in ABREV_PATHS:
    try:
        if p and Path(p).exists():
            with open(p, 'r', encoding='utf-8') as f:
                ABREV = json.load(f)
                break
    except Exception:
        ABREV = {}
        break

# ---------------------------
# Formatação de abreviaturas
# ---------------------------
def _escape_for_regex(s: str) -> str:
    return re.escape(s)

_abbrev_list_sorted = sorted(list(ABREV.keys()), key=lambda x: -len(x))
_abbrev_patterns = [r"(?<!\w)" + _escape_for_regex(a) + r"(?!\w)" for a in _abbrev_list_sorted]
ABREV_REGEX = re.compile(r"(" + r"|".join(_abbrev_patterns) + r")") if _abbrev_patterns else None

def format_abrevs(texto: str) -> str:
    """Substitui abreviaturas por spans com classes e tooltip. Usar apenas no dicionário."""
    if not texto or not ABREV_REGEX:
        return texto

    def _repl(m):
        ab = m.group(0)
        info = ABREV.get(ab, {}) if ABREV else {}
        desc = info.get("descricao", "") if isinstance(info, dict) else ""
        tipo = info.get("tipo", "") if isinstance(info, dict) else ""
        cls = "autor-sc" if ("Autor" in tipo or "Obras" in tipo or "Nome" in tipo or "Cultural" in tipo) else "abrev"
        title = desc.replace('"', '&quot;')
        return f'<span class="{cls}" title="{title}">{ab}</span>'

    return ABREV_REGEX.sub(_repl, texto)

# ---------------------------
# format_pdesc: quebras apos ♦ (mantém '♦ label' na mesma linha)
# ---------------------------
def format_pdesc(pdesc: str) -> str:
    if not pdesc:
        return ""
    # Normalize line endings
    p = pdesc.replace('\r\n', '\n').replace('\r', '\n')
    # Ensure diamonds followed by a space keep label on same line
    # replace '♦ ' with a span and a following space; keep '♦' alone untouched if no label follows
    p = re.sub(r'♦\s+', '<br><span class="ddgp-sec">♦</span> ', p)
    # apply abrevs formatting
    p = format_abrevs(p)
    # preserve simple newlines as <br/>
    p = p.replace('\n', '<br/>')
    return p

# ---------------------------
# Transliteration ASCII -> Greek (basic)
# ---------------------------
def latin_to_basic_grc(s: str) -> str:
    """Transliteração ASCII básica -> grego sem acentos (hipatia-style)."""
    if not s:
        return s
    s = "".join(ch for ch in s if not ch.isdigit())
    table = {
        "a":"α","b":"β","g":"γ","d":"δ",
        "e":"ε","z":"ζ","h":"η","q":"θ",
        "i":"ι","k":"κ","l":"λ","m":"μ",
        "n":"ν","c":"ξ","o":"ο","p":"π",
        "r":"ρ","s":"σ","t":"τ","u":"υ",
        "f":"φ","x":"χ","y":"ψ","w":"ω",
    }
    out = []
    prev = ""
    for ch in s:
        # treat spaces to produce final sigma ς when appropriate
        if ch == " " and prev == "σ":
            out[-1] = "ς"
            out.append(" ")
            prev = " "
            continue
        gr = table.get(ch, ch)
        out.append(gr)
        prev = gr
    if out and out[-1] == "σ":
        out[-1] = "ς"
    return "".join(out)

# ---------------------------
# Funções de analise e fallback (import morph if available)
# ---------------------------
MORPH_AVAILABLE = False
try:
    from ddgp.morph_simple import morph_analyze_simple
    MORPH_AVAILABLE = True
except Exception as e:
    morph_analyze_simple = None
    st.warning("morph_simple não pôde ser importado — a análise morfológica ficará indisponível. Erro: " + str(e))

# Função para encontrar todos os entry ids correspondentes a um candidato de lema
def find_entry_ids_for_lemma_candidate(cand: str):
    if not cand:
        return []
    base = simplify(cand)
    results = []
    seen = set()
    # busca direta
    if base in DDGP_INDEX_LEMAS:
        eid = DDGP_INDEX_LEMAS[base]
        if eid not in seen:
            results.append(eid); seen.add(eid)
    # variantes unicode
    for variant in (unicodedata.normalize("NFC", base), unicodedata.normalize("NFD", base)):
        if variant in DDGP_INDEX_LEMAS:
            eid = DDGP_INDEX_LEMAS[variant]
            if eid not in seen:
                results.append(eid); seen.add(eid)
    # fallback: procurar chaves que comecem com base (capta lemas numerados)
    for k, eid in DDGP_INDEX_LEMAS.items():
        try:
            k_simp = unicodedata.normalize("NFD", k)
            k_simp = "".join(ch for ch in k_simp if not unicodedata.combining(ch)).lower()
            k_simp = "".join(ch for ch in k_simp if not ch.isdigit())
        except Exception:
            k_simp = k
        if k_simp.startswith(base):
            if eid not in seen:
                results.append(eid); seen.add(eid)
    return results

# ---------------------------
# HEADER / LOGO
# ---------------------------
col_left, col_title = st.columns([1, 10])
with col_left:
    try:
        if LOGO_LOCAL and os.path.exists(os.path.join(BASE_DIR, LOGO_LOCAL)):
            st.image(os.path.join(BASE_DIR, LOGO_LOCAL), width=64)
        else:
            st.image(LOGO_URL, width=64)
    except Exception:
        st.text("")
with col_title:
    st.markdown("## DDGP Plus — Analisador Morfológico e Dicionário Digital de Grego–Português")
    st.markdown("Versão 2025 — online")
st.markdown("---")

# ---------------------------
# INPUT: single input that converts latin keystrokes to greek visually
# We'll intercept user typing and update session_state so the field shows greek.
# ---------------------------
if "campo_ascii" not in st.session_state:
    st.session_state["campo_ascii"] = ""
if "campo_grc" not in st.session_state:
    st.session_state["campo_grc"] = ""

def _on_change_convert():
    txt = st.session_state.get("campo_ascii", "")
    # if ascii-only, transliterate and set campo_ascii to greek so user sees greek characters
    if txt and all(ord(ch) < 128 for ch in txt):
        gr = latin_to_basic_grc(txt.lower())
        # update both ascii and grc to the greek form so the input shows greek
        st.session_state["campo_ascii"] = gr
        st.session_state["campo_grc"] = gr
    else:
        # already greek, just normalize
        st.session_state["campo_grc"] = txt

# Single visible input: user types (latin or greek) and sees greek
st.text_input(
    "Digite (pode usar letras latinas: legw, ferw, akouw — ou grego diretamente):",
    key="campo_ascii",
    on_change=_on_change_convert
)

# internal word used by the pipeline (always greek)
palavra = st.session_state.get("campo_grc", "").strip()

# ---------------------------
# MAIN: processa quando houver palavra
# ---------------------------
if palavra:
    st.subheader("🧩 Resultado")

    # 1) Try exact form lookup in ddgp_index_formas (fast path)
    simp_form = simplify(palavra)
    found_entries = []
    if DDGP_INDEX_FORMAS and simp_form in DDGP_INDEX_FORMAS:
        ids = DDGP_INDEX_FORMAS[simp_form]
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

    # fallback: try to heuristically derive lemma from common verbal endings
    form_base = simplify(palavra)
    if form_base.endswith("ουσιν"):
        lemma_candidates.append(form_base[:-5])
    # remove duplicates keeping order
    seen = set(); lemma_candidates = [x for x in lemma_candidates if not (x in seen or seen.add(x))]

    # If dictionary entries were found by exact form, show them first
    if found_entries:
        st.subheader("📘 Entradas do DDGP (lookup por forma)")
        for ent in found_entries:
            gid = ent.get("id","?")
            gword = ent.get("gword","")
            pdesc = ent.get("pdesc","")
            pdesc_fmt = format_pdesc(pdesc)
            st.markdown(f"**{gword}** (id: {gid})")
            st.markdown(pdesc_fmt, unsafe_allow_html=True)

    elif lemma_candidates:
        st.subheader("📘 Lookup por lema candidato")
        matched_any = False
        for cand in lemma_candidates:
            # busca todos os entry ids correspondentes (inclui lemas numerados)
            entry_ids = find_entry_ids_for_lemma_candidate(cand)
            if not entry_ids:
                st.info(f"Nenhuma entrada encontrada no índice para o lema candidato: **{cand}**")
                continue
            matched_any = True
            for entry_id in entry_ids:
                ent = DDGP_ENTRY.get(str(entry_id))
                if ent:
                    gword = ent.get("gword", "")
                    pdesc = ent.get("pdesc", "")
                    pdesc_fmt = format_pdesc(pdesc)
                    st.markdown(f"**{gword}** (id: {entry_id})")
                    st.markdown(pdesc_fmt, unsafe_allow_html=True)
                else:
                    st.warning(f"Entrada {entry_id} ausente no JSON.")
        if not matched_any:
            st.warning("Nenhuma entrada do DDGP encontrada para a(s) forma(s) ou lema(s) candidatos.")
    else:
        st.warning("Nenhuma entrada do DDGP encontrada para esta forma ou lema.")

# --- FOOTER ---
st.markdown("---")
footer_short = """
**DDGP Plus** — Analisador Morfológica e Dicionário Digital de Grego–Português.  
Versão 2025. Disponível em: https://ddgp-plus.streamlit.app  
Baseado no Dicionário Digital de Grego–Português (DDGP e DGP), pelo Projeto Letras Clássicas Digitais FCLAr/UNESP .
Licenciado sob **CC BY–NC–ND 4.0**.
"""
footer_long = """
**Créditos e licença (detalhado)**

- Base: Dicionário Digital de Grego–Português (DDGP e DGP), Projeto Letras Clássicas Digitais — FCLAr/UNESP.  
- Responsável: Anise D'Orange Ferreira.
- Licença do conteúdo digital: CC BY–NC–ND 4.0.  
- Créditos aos autores da versião impressa do DGP, coordenadores e instituições conforme rodapé em http://hipatia.fclar.unesp.br.  
- Desenvolvimento do front-end e integração: equipe de desenvolvimento (registro técnico disponível sob solicitação).
"""
st.markdown(footer_short)
with st.expander("Créditos e licença (detalhado)"):
    st.markdown(footer_long)
st.markdown("<div style='text-align:right; font-size:0.85em; color:gray;'>© Projeto DDGP — UNESP (digital). CC BY–NC–ND 4.0</div>", unsafe_allow_html=True)
