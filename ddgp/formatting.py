# ddgp/formatting.py
# -*- coding: utf-8 -*-
"""
Funções de formatação de texto para o Dicionário.
"""
import re
import os
import json

BASE_DIR = os.path.dirname(__file__)
DDGP_DATA_DIR = os.path.join(BASE_DIR, "data")

# --- Carregamento de Abreviaturas ---
try:
    with open(os.path.join(DDGP_DATA_DIR, "abrev.json"), "r", encoding="utf-8") as f:
        ABREV = json.load(f)
except FileNotFoundError:
    print("ATENÇÃO: Arquivo abrev.json não encontrado. A formatação de abreviaturas será desativada.")
    ABREV = {}

# --- Lógica de Abreviaturas ---
def _escape_for_regex(s: str) -> str:
    return re.escape(s)

_abbrev_list_sorted = sorted(list(ABREV.keys()), key=lambda x: -len(x))
_abbrev_patterns = [r"(?<!\w)" + _escape_for_regex(a) + r"(?!\w)" for a in _abbrev_list_sorted]
ABREV_REGEX = re.compile(r"(" + r"|".join(_abbrev_patterns) + r")") if _abbrev_patterns else None

def format_abrevs(texto: str) -> str:
    """Substitui abreviaturas por spans com classes e tooltip."""
    if not texto or not ABREV_REGEX:
        return texto

    def _repl(m):
        ab = m.group(0)
        info = ABREV.get(ab, {}) if ABREV else {}
        desc = info.get("descricao", "") if isinstance(info, dict) else ""
        tipo = info.get("tipo", "") if isinstance(info, dict) else ""
        
        # Lógica de classificação
        cls = "abrev"
        if ("Autor" in tipo or "Obras" in tipo or "Nome" in tipo or "Cultural" in tipo):
            cls = "autor-sc"
            
        title = desc.replace('"', '&quot;')
        return f'<span class="{cls}" title="{title}">{ab}</span>'

    return ABREV_REGEX.sub(_repl, texto)

# --- Formatação de Parágrafos de Descrição ---
def format_pdesc(pdesc: str) -> str:
    """Formata texto de descrição, tratando quebras de linha e aplicando formatação de abreviaturas."""
    if not pdesc:
        return ""
        
    # Normalize line endings
    p = pdesc.replace('\r\n', '\n').replace('\r', '\n')
    
    # 1. Substitui '♦ ' por <br> e span com classe ddgp-sec (para quebra de linha após o diamante)
    # Garante que '♦ label' fique na mesma linha usando um espaço após o <br>
    p = re.sub(r'♦\s+', '<br><span class="ddgp-sec">♦</span> ', p)
    
    # 2. Aplica formatação de abreviaturas
    p = format_abrevs(p)
    
    # 3. Preserva newlines simples como <br/>
    p = p.replace('\n', '<br/>')
    
    return p