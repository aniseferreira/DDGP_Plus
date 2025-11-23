# app.py
# -*- coding: utf-8 -*-

import streamlit as st
import os
import json
from ddgp.morph_simple import morph_analyze_simple 
# Presumimos que o ddgp/translit.py existe e possui a função transliterate_to_greek
from ddgp.translit import transliterate_to_greek 

# --- Configurações Iniciais, Títulos e HEADER ---

BASE_DIR = os.path.dirname(__file__)
DDGP_DATA_DIR = os.path.join(BASE_DIR, "ddgp", "data")
STYLE_DIR = os.path.join(BASE_DIR, "ddgp", "style") # Novo diretório para estilos

# 1. Configuração da Página (Título da Aba e Layout)
st.set_page_config(
    page_title="DDGP + Morfologia Grega",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 2. CARREGAMENTO DOS ESTILOS CSS
def load_and_inject_css(filename):
    """Carrega e injeta um arquivo CSS no Streamlit."""
    try:
        css_path = os.path.join(STYLE_DIR, filename)
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"Arquivo de estilo CSS não encontrado: ddgp/style/{filename}.")

# Carrega os dois arquivos CSS fornecidos
load_and_inject_css("style.css")
load_and_inject_css("style_map.css")


# 3. HEADER/TÍTULO PRINCIPAL (Usando st.title e st.markdown para classes)
st.title("📚 DDGP + Análise Morfológica Grega")
st.markdown(
    """
    <p id="ddgp-instrucao">Ferramenta para análise de formas gregas e consulta rápida ao Dicionário de Dupla Gramática do Português (DDGP).</p>
    """, 
    unsafe_allow_html=True
)


# 4. Definição do FOOTER
# Usamos a classe .footer-ddgp definida no style.css
footer_html = """
<style>
/* Oculta o menu Streamlit e o footer padrão */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
<div class="footer-ddgp">
    Desenvolvido para análise de Grego Antigo | Baseado em DDGP | Projeto Acadêmico.
</div>
"""
# Adicionamos o footer customizado no final da página
st.markdown(footer_html, unsafe_allow_html=True)


# --- Funções de Carregamento de Dados DDGP (Mantido) ---

@st.cache_resource
def load_ddgp_data():
    """Carrega os dados do DDGP na memória."""
    try:
        with open(os.path.join(DDGP_DATA_DIR, "ddgp3x_entry.json"), "r", encoding="utf-8") as f:
            entries = json.load(f)
        
        with open(os.path.join(DDGP_DATA_DIR, "ddgp_index_lemas.json"), "r", encoding="utf-8") as f:
            lema_index = json.load(f)
        
        with open(os.path.join(DDGP_DATA_DIR, "ddgp_index_formas_final.json"), "r", encoding="utf-8") as f:
            forma_index = json.load(f)
        
        return entries, lema_index, forma_index
    except FileNotFoundError as e:
        st.error(f"Erro ao carregar arquivos de dados do DDGP: {e.filename}. Verifique a pasta ddgp/data.")
        return {}, {}, {}

DDGP_ENTRIES, DDGP_LEMA_INDEX, DDGP_FORMA_INDEX = load_ddgp_data()


# --- Funções de Busca (Mantido) ---

def lookup_ddgp_by_lema(lema):
    """Busca a entrada DDGP usando o lema fornecido pelo parser."""
    if lema in DDGP_LEMA_INDEX:
        ddgp_key = DDGP_LEMA_INDEX[lema]
        return DDGP_ENTRIES.get(ddgp_key)
    return None

# --- Interface e Lógica Principal ---

st.markdown('<div class="section-title">Insira a Palavra</div>', unsafe_allow_html=True) 

input_text = st.text_input(
    "Digite a palavra grega (pode usar letras latinas: legw, ferw, akouw):",
    key="input_word"
)

# --- Processamento e Exibição ---

if input_text:
    
    # 1. Transliteração 
    try:
        greek_word = transliterate_to_greek(input_text)
    except Exception:
        greek_word = input_text 

    st.markdown("---")
    st.markdown('<div class="section-title">🧩 Resultado da Análise Morfológica</div>', unsafe_allow_html=True)

    # 2. Análise Morfológica
    morph_result = morph_analyze_simple(greek_word)

    # Usa uma box de resultado definida no style_map.css
    st.markdown('<div class="result-box">', unsafe_allow_html=True)
    st.json(morph_result)
    st.markdown('</div>', unsafe_allow_html=True)


    # 3. Busca no DDGP 
    lema_candidato = morph_result.get("lema")

    st.markdown("---")
    st.markdown('<div class="section-title">📘 Lookup do DDGP</div>', unsafe_allow_html=True)

    if lema_candidato and lema_candidato not in ("desconhecido", "none"):
        
        ddgp_entry = lookup_ddgp_by_lema(lema_candidato)

        if ddgp_entry:
            st.success(f"Entrada DDGP encontrada para o lema: **{lema_candidato}**")
            
            # Formatação do resultado do Dicionário (Usando classes do style.css)
            st.markdown(f'<h2 style="color: var(--ddgp-azul);">{ddgp_entry.get("headword", lema_candidato)}</h2>', unsafe_allow_html=True)
            st.markdown(f"<p class='etimo'>**Tradução:** *{ddgp_entry.get('translation', 'N/A')}*</p>", unsafe_allow_html=True)
            st.markdown(f"<p class='abrev'>**Info Gramatical:** {ddgp_entry.get('grammar_info', 'N/A')}</p>", unsafe_allow_html=True)
            
        else:
            st.warning(f"Nenhuma entrada encontrada no índice para o lema candidato: **{lema_candidato}**")
            st.info("Nenhuma entrada do DDGP encontrada para a(s) forma(s) ou lema(s) candidatos.")
    else:
        st.info("A análise morfológica não identificou um lema válido para pesquisa no DDGP.")
