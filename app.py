# app.py — DDGP Plus (versão simples + dicionário)

import streamlit as st
import json, os, unicodedata

# -------------------------
# Importa o analisador morfológico simples
# -------------------------
from ddgp.morph_simple import morph_analyze_simple, simplify, normalize

# -------------------------
# Localização dos arquivos DDGP
# -------------------------
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "ddgp", "data")

def load_json(name):
    path = os.path.join(DATA_DIR, name)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# Carrega todos os índices
DDGP_ENTRIES = load_json("ddgp3x_entry.json")
INDEX_LEMAS = load_json("ddgp_index_lemas.json")
INDEX_FORMAS = load_json("ddgp_index_formas_final.json")
FORMA_TO_LEMA = load_json("ddgp_forma_to_lema.json")

# -------------------------
# Função de lookup no dicionário
# -------------------------
def buscar_ddgp_por_lema(lema_simplificado):
    """Retorna lista de entradas DDGP cujo lema corresponde ao lema simplificado."""
    if lema_simplificado in INDEX_LEMAS:
        id_ = INDEX_LEMAS[lema_simplificado]
        ent = DDGP_ENTRIES.get(id_)
        return [ent] if ent else []
    return []

def buscar_ddgp_por_forma(form_simplificada):
    """Busca entradas cujas formas aparecem em gword (index de variantes)."""
    ids = INDEX_FORMAS.get(form_simplificada, [])
    return [DDGP_ENTRIES[i] for i in ids if i in DDGP_ENTRIES]

# -------------------------
# Interface Streamlit
# -------------------------
st.title("📘 DDGP Plus — Analisador Morfológico + Dicionário")
st.write("Digite uma forma grega politônica ou sem diacríticos.")

palavra = st.text_input("Forma grega:")

if palavra:
    st.subheader("🧩 Análise morfológica")
    resultado = morph_analyze_simple(palavra)
    st.json(resultado)

    st.subheader("📘 Dicionário DDGP")

    simp = simplify(palavra)

    # 1) lookup direto pela forma
    entradas = buscar_ddgp_por_forma(simp)

    # 2) lookup pelo lema identificado pela morfologia
    if not entradas and resultado.get("lema"):
        lema_simp = simplify(resultado["lema"])
        entradas = buscar_ddgp_por_lema(lema_simp)

    # 3) fallback: forma → lema mapeado
    if not entradas and simp in FORMA_TO_LEMA:
        lema_simp = FORMA_TO_LEMA[simp]
        entradas = buscar_ddgp_por_lema(lema_simp)

    # Exibição
    if entradas:
        for e in entradas:
            st.markdown(f"### **{e['gword']}** (ID {e['id']})")
            st.markdown(
    """
    <hr>

    <div style="font-size: 0.9rem; line-height: 1.35;">
    <strong>DDGP Plus — Analisador Morfológico e Dicionário Digital de Grego-Português.</strong><br>
    Versão 2025. Disponível em:
    <a href="https://ddgp-plus.streamlit.app" target="_blank">https://ddgp-plus.streamlit.app</a>.
    <br><br>

    Baseado no <em>Dicionário Digital de Grego-Português</em> (DDGP e DGP),
    Projeto <strong>Letras Clássicas Digitais / UNESP</strong>.<br>

    Licenciado sob <strong>CC BY–NC–ND 4.0</strong>.
    </div>

    """,
    unsafe_allow_html=True
)

            st.write(e["pdesc"])
    else:
        st.error("Nenhuma entrada do DDGP encontrada para esta forma ou lema.")


