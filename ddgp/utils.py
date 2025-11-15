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
# -----------------------------------------------------------
