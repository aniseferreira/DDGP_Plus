# -*- coding: utf-8 -*-
"""
DDGP Plus — Lexicon module
Carrega os índices e as entradas do dicionário localmente a partir de /ddgp/data/.
Oferece:
- lookup por forma
- lookup por lema
- remissão forma → lema
- listagem das formas associadas a um lema
- busca sem diacríticos
- fallback fuzzy simples
"""

import json
import unicodedata
import os


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def normalize(s: str) -> str:
    """Normaliza Unicode para NFC e remove espaços extras."""
    return unicodedata.normalize("NFC", s or "").strip()


def simplify(s: str) -> str:
    """Remove diacríticos e baixa para minúsculas."""
    s = normalize(s)
    s = "".join(
        ch for ch in unicodedata.normalize("NFD", s)
        if not unicodedata.combining(ch)
    )
    return s.lower()


def similarity(a: str, b: str) -> float:
    """Pequena métrica simples para fuzzy: razão de coincidência."""
    a, b = simplify(a), simplify(b)
    if not a or not b:
        return 0.0
    matches = sum(1 for x, y in zip(a, b) if x == y)
    return matches / max(len(a), len(b))


# ---------------------------------------------------------------------------
# Carregamento dos dados
# ---------------------------------------------------------------------------

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

def load_json(name: str):
    path = os.path.join(DATA_DIR, name)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# Entradas completas (id → entry)
ENTRIES = load_json("ddgp3x_entry.json")

# Índice principal de formas (grafias e simplificadas → ids)
INDEX_FORMAS = load_json("ddgp_index_formas_final.json")

# Mapeamento de lemas (simplificado → id)
INDEX_LEMAS = load_json("ddgp_index_lemas.json")

# Relação forma_id → lema_id
FORMA_TO_LEMA = load_json("ddgp_forma_to_lema.json")


# ---------------------------------------------------------------------------
# Funções principais de lookup
# ---------------------------------------------------------------------------

def lookup_form(term: str):
    """
    Busca literal de uma forma. Retorna lista de IDs.
    - tenta forma exata
    - tenta forma simplificada
    - fallback fuzzy
    """
    term_n = normalize(term)
    term_s = simplify(term)

    # 1. exato
    if term_n in INDEX_FORMAS:
        return INDEX_FORMAS[term_n]

    # 2. simplificado
    if term_s in INDEX_FORMAS:
        return INDEX_FORMAS[term_s]

    # 3. fallback fuzzy
    candidates = []
    for key in INDEX_FORMAS.keys():
        if similarity(term, key) >= 0.6:
            for rid in INDEX_FORMAS[key]:
                candidates.append(rid)
    return list(sorted(set(candidates)))


def lookup_lemma(term: str):
    """
    Busca lema principal:
    - apenas formas canônicas simplificadas
    - retorna ID ou None
    """
    key = simplify(term)
    return INDEX_LEMAS.get(key, None)


def get_entry(rid: int | str):
    """Retorna o verbete completo (gword + pdesc) para um ID."""
    rid = str(rid)
    return ENTRIES.get(rid, None)


def get_lemma_id_for_form(rid: int | str):
    """Retorna o lema principal associado a um id de forma."""
    rid = str(rid)
    return FORMA_TO_LEMA.get(rid, None)


def get_forms_for_lemma(lema_id: int | str):
    """Retorna todos os IDs que têm lema_id como lema principal."""
    lema_id = str(lema_id)
    result = []
    for form_id, lemma_ref in FORMA_TO_LEMA.items():
        if str(lemma_ref) == lema_id or form_id == lema_id:
            result.append(form_id)
    return sorted(result)


# ---------------------------------------------------------------------------
# Função unificada de busca
# ---------------------------------------------------------------------------

def search(term: str):
    """
    Busca unificada:
    1) tenta encontrar pelo lema
    2) tenta encontrar pela forma literal
    3) fallback fuzzy
    Retorna dict com:
       {
         "input": ...,
         "lemma_id": ...,
         "lemma_entry": ...,
         "matched_form_ids": [...],
         "form_entries": [...]
       }
    """

    term_n = normalize(term)
    term_s = simplify(term)

    # 1. Tenta lema diretamente
    lemma_id = lookup_lemma(term)
    if lemma_id:
        return {
            "input": term,
            "lemma_id": lemma_id,
            "lemma_entry": get_entry(lemma_id),
            "matched_form_ids": get_forms_for_lemma(lemma_id),
            "form_entries": [get_entry(fid) for fid in get_forms_for_lemma(lemma_id)],
        }

    # 2. Tenta forma literal
    form_ids = lookup_form(term)
    if form_ids:
        # tenta achar lema através da primeira forma encontrada
        first_form = str(form_ids[0])
        lemma_from_form = get_lemma_id_for_form(first_form)

        return {
            "input": term,
            "lemma_id": lemma_from_form,
            "lemma_entry": get_entry(lemma_from_form) if lemma_from_form else None,
            "matched_form_ids": form_ids,
            "form_entries": [get_entry(fid) for fid in form_ids],
        }

    # 3. Nada encontrado
    return {
        "input": term,
        "lemma_id": None,
        "lemma_entry": None,
        "matched_form_ids": [],
        "form_entries": []
    }


# ---------------------------------------------------------------------------
# Fim
# ---------------------------------------------------------------------------
