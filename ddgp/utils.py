# -*- coding: utf-8 -*-

import unicodedata
import regex as re

# ------------------------------------------------------------
# Normalização Unicode
# ------------------------------------------------------------

def normalize_unicode(word: str) -> str:
    """
    Normaliza a palavra para NFC.
    """
    if not word:
        return ""
    return unicodedata.normalize("NFC", word)


# ------------------------------------------------------------
# Remoção leve de diacríticos (para buscas mais amplas)
# Mantém as letras gregas, remove apenas acentos.
# ------------------------------------------------------------

DIACRITICS_PATTERN = re.compile(r"[\p{M}]+")

def remove_diacritics(word: str) -> str:
    """
    Remove marcas combinantes (tonos, espíritos, iota subscrito).
    Mantém o alfabeto grego.
    """
    if not word:
        return ""
    decomposed = unicodedata.normalize("NFD", word)
    stripped = DIACRITICS_PATTERN.sub("", decomposed)
    return unicodedata.normalize("NFC", stripped)


# ------------------------------------------------------------
# Simplificação básica para comparação
# ------------------------------------------------------------

def simplify(word: str) -> str:
    """
    Simplifica uma palavra:
    - normaliza
    - remove diacríticos
    - põe em minúsculas
    """
    if not word:
        return ""
    w = normalize_unicode(word)
    w = remove_diacritics(w)
    return w.lower()


# ------------------------------------------------------------
# Distância de Levenshtein simples
# (para sugestões aproximadas no léxico)
# ------------------------------------------------------------

def levenshtein(a: str, b: str) -> int:
    """
    Distância mínima entre duas strings.
    Implementação leve (sem dependências externas).
    """
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)

    m = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]

    for i in range(len(a) + 1):
        m[i][0] = i
    for j in range(len(b) + 1):
        m[0][j] = j

    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            m[i][j] = min(
                m[i - 1][j] + 1,      # deleção
                m[i][j - 1] + 1,      # inserção
                m[i - 1][j - 1] + cost   # substituição
            )

    return m[-1][-1]


# ------------------------------------------------------------
# Sugestões fuzzy (para palavras não achadas no léxico)
# ------------------------------------------------------------

def fuzzy_suggestions(word: str, candidates: list, max_suggestions=5):
    """
    Retorna uma lista de candidatos aproximados.
    """
    word_s = simplify(word)
    scored = []

    for cand in candidates:
        dist = levenshtein(word_s, simplify(cand))
        scored.append((dist, cand))

    scored.sort(key=lambda x: x[0])
    return [c for _, c in scored[:max_suggestions]]

