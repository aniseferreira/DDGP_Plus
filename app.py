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


# ------------------------------------------------------------
# Carregar CSS customizado (inserido automaticamente)
# Coloque style.css e style_map.css em /ddgp/style/
# ------------------------------------------------------------
from pathlib import Path

def load_css(file_name: str):
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            css = f"<style>{f.read()}</style>"
            st.markdown(css, unsafe_allow_html=True)
    except FileNotFoundError:
        # arquivo de estilo não encontrado; continuar sem falha
        pass

# paths recomendados
style_main = "ddgp/style/style.css"
style_map = "ddgp/style/style_map.css"

# carregar se existirem
if Path(style_main).exists():
    load_css(style_main)
if Path(style_map).exists():
    load_css(style_map)

# Também carrega se estiver na raiz (para desenvolvimento local)
if Path("style.css").exists():
    load_css("style.css")
if Path("style_map.css").exists():
    load_css("style_map.css")

# --- Inline fallback CSS (garante estilos mesmo se style.css falhar) ---
_inline_css = """
<style>
/* Abreviaturas gramaticais */
.abrev {
    font-style: italic;
    color: #0066cc;
    cursor: help;
}

/* Abreviaturas de autores/obras (small caps) */
.autor-sc {
    font-variant: small-caps;
    letter-spacing: 0.4px;
    cursor: help;
}

/* Seções do dicionário (♦ ativa, ♦ média, ♦ passiva) */
.ddgp-sec {
    font-weight: 600;
    margin-top: 0.8em;
    margin-bottom: 0.0em;
    font-size: 1.02em;
}

/* Parágrafo de sentido/definição logo após o marcador */
.ddgp-mean {
    margin-top: 0.2em;
    margin-bottom: 0.6em;
}

/* Garante que spans com title mostrem pointer e não sejam afetados por reset CSS */
.abrev, .autor-sc { text-decoration: none; }
.abrev[title], .autor-sc[title] { position: relative; }
</style>
"""
st.markdown(_inline_css, unsafe_allow_html=True)


# ======= Carregar abreviaturas (abrev.json) =======
# Procura primeiro no diretório do projeto, depois em /mnt/data (ambiente de desenvolvimento)
ABREV_PATHS = ["ddgp/data/abrev.json", "ddgp/abrev.json", "abrev.json", "/mnt/data/abrev.json"]
ABREV = {}
for p in ABREV_PATHS:
    try:
        with open(p, 'r', encoding='utf-8') as f:
            ABREV = json.load(f)
            break
    except FileNotFoundError:
        continue
    except Exception:
        ABREV = {}
        break

# ======= Função de formatação de abreviaturas =======
# Implementação simples e robusta que evita substituir partes de palavras:
import re

def _escape_for_regex(s: str) -> str:
    return re.escape(s)

# Ordena por comprimento decrescente para evitar colisões (e.g., 'pl.' vs 'plín.')
_abbrev_list_sorted = sorted(list(ABREV.keys()), key=lambda x: -len(x))
_abbrev_patterns = [r"(?<!\w)" + _escape_for_regex(a) + r"(?!\w)" for a in _abbrev_list_sorted]

if _abbrev_patterns:
    ABREV_REGEX = re.compile(r"(" + r"|".join(_abbrev_patterns) + r")")
else:
    ABREV_REGEX = None

def format_abrevs(texto: str) -> str:
    """Substitui abreviaturas por spans com classes e tooltip. Usar apenas no dicionário."""
    if not texto or not ABREV_REGEX:
        return texto

    def _repl(m):
        ab = m.group(0)
        info = ABREV.get(ab, {})
        desc = info.get("descricao", "")
        tipo = info.get("tipo", "")

        # autores/obras/culturais = small caps
        cls = "autor-sc" if ("Autor" in tipo or "Obras" in tipo or "Nome" in tipo or "Cultural" in tipo) else "abrev"

        title = desc.replace('"', '&quot;')
        return f'<span class="{cls}" title="{title}">{ab}</span>'

    return ABREV_REGEX.sub(_repl, texto)


import re

def format_pdesc(pdesc: str) -> str:
    """
    Transforma o pdesc para:
      <p class='ddgp-sec'>♦ ativa</p>
      <p class='ddgp-mean'>...texto da ativa...</p>
    e aplica format_abrevs() ao conteúdo.
    """

    if not pdesc:
        return ""

    text = pdesc.strip()

    # Normaliza espaços em branco
    text = re.sub(r"\s+", " ", text)

    # Padrão para encontrar os marcadores ♦ com rótulos (ativa|média|passiva)
    # Captura '♦' + espaço opcional + rótulo + resto até próximo '♦' (lookahead)
    pattern = re.compile(r"♦\s*(ativa|m[eé]dia|passiva)\s*(?=(?:.*?♦)|$)", re.IGNORECASE)

    # Se não encontrar marcadores bem formados, só aplica abreviaturas e devolve
    if not pattern.search(text):
        # aplicar abreviaturas ao texto inteiro
        return format_abrevs(text)

    parts = []
    # vamos percorrer ocorrências e pegar fatias
    last_idx = 0
    for m in pattern.finditer(text):
        start = m.start()
        # texto antes do marcador (pode conter prefixo, ex.: paradigmas)
        if start > last_idx:
            before = text[last_idx:start].strip()
            if before:
                parts.append(("body", before))
        label = m.group(1).strip()
        # a seção começa no m.end(); precisamos até o próximo marcador ou fim
        # procurar próxima ocorrência a partir de m.end()
        next_m = pattern.search(text, m.end())
        if next_m:
            section_text = text[m.end():next_m.start()].strip()
            last_idx = next_m.start()
        else:
            section_text = text[m.end():].strip()
            last_idx = len(text)
        # adiciona marcador + conteúdo
        parts.append(("marker", "♦ " + label))
        parts.append(("mean", section_text))

    # Caso reste texto após o último marcador
    if last_idx < len(text):
        tail = text[last_idx:].strip()
        if tail:
            parts.append(("tail", tail))

    # Construir HTML final
    out_fragments = []
    for kind, val in parts:
        if kind == "body":
            # corpo antes de marcadores (por exemplo, paradigma), aplicar abrevs e manter
            out_fragments.append(f"<p>{format_abrevs(val)}</p>")
        elif kind == "marker":
            # marcador numa linha com label
            out_fragments.append(f"<p class='ddgp-sec'>{val}</p>")
        elif kind == "mean":
            # parágrafo de sentido
            out_fragments.append(f"<p class='ddgp-mean'>{format_abrevs(val)}</p>")
        elif kind == "tail":
            out_fragments.append(f"<p>{format_abrevs(val)}</p>")

    return "\n".join(out_fragments)
    
   

# helper utils
def normalize(text):
    return unicodedata.normalize("NFC", (text or "")).strip()

def simplify(text):
    s = normalize(text)
    s = "".join(ch for ch in unicodedata.normalize("NFD", s)
                if not unicodedata.combining(ch))
    s = s.lower()

    # remover dígitos
    s = "".join(ch for ch in s if not ch.isdigit())

    # opcional: remover ponto, traço, barra
    for ch in [".", "-", "/", " "]:
        s = s.replace(ch, "")

    return s

def find_entry_ids_for_lemma_candidate(cand: str):
    """
    Dado um candidato de lema (em grego, poss. com/sem dígito),
    devolve ids de entradas correspondentes no DDGP:
      - busca direta
      - busca por normalização Unicode
      - busca por prefixo (captura lemas numerados λέγω1, λέγω2 etc.)
    """
    if not cand:
        return []

    base = simplify(cand)  # já remove diacríticos e dígitos

    results = []
    seen = set()

    # 1 — tentativa direta
    if base in DDGP_INDEX_LEMAS:
        eid = DDGP_INDEX_LEMAS[base]
        results.append(eid)
        seen.add(eid)

    # 2 — normalizações Unicode
    for variant in (unicodedata.normalize("NFC", base),
                    unicodedata.normalize("NFD", base)):
        if variant in DDGP_INDEX_LEMAS:
            eid = DDGP_INDEX_LEMAS[variant]
            if eid not in seen:
                results.append(eid); seen.add(eid)

    # 3 — fallback: buscar todos que começam com o lema simplificado
    for k, eid in DDGP_INDEX_LEMAS.items():
        # normalizar chave
        k_simp = "".join(
            ch for ch in unicodedata.normalize("NFD", k)
            if not unicodedata.combining(ch)
        ).lower()
        k_simp = "".join(ch for ch in k_simp if not ch.isdigit())

        if k_simp.startswith(base) and eid not in seen:
            results.append(eid); seen.add(eid)

    return results

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

            # aplica quebra após ♦
            st.markdown(f"**{gword}** (id: {gid})")

            pdesc_fmt = format_pdesc(pdesc)
            st.write(pdesc_fmt, unsafe_allow_html=True)

    elif lemma_candidates:
        st.subheader("📘 Lookup por lema candidato")
        matched_any = False
        for cand in lemma_candidates:
            if cand in DDGP_INDEX_LEMAS:
                matched_any = True
                entry_id = DDGP_INDEX_LEMAS[cand]
                ent = DDGP_ENTRY.get(str(entry_id))
                if ent:
                    gword = ent.get("gword", "")
                    pdesc = ent.get("pdesc", "")

                    st.markdown(f"**{gword}** (id: {entry_id})")

                    pdesc_fmt = format_pdesc(pdesc)
                    st.write(pdesc_fmt, unsafe_allow_html=True)


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
Baseado no Dicionário Digital de Grego-Português (DDGP e DGP), pelo Projeto Letras Clássicas Digitais FCLAr/UNESP .
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

# place footer in a container so HTML injection is minimal (no custom CSS)
st.markdown("---")
st.markdown(footer_short)
with st.expander("Créditos e licença (detalhado)"):
    st.markdown(footer_long)

# small copyright note aligned right
st.markdown("<div style='text-align:right; font-size:0.85em; color:gray;'>© Projeto DDGP — UNESP (digital). CC BY–NC–ND 4.0</div>", unsafe_allow_html=True)
