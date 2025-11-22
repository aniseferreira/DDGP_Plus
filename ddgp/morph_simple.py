# morph_simple.py — Versão B2 (heurísticas conservadoras aprimoradas)
# -*- coding: utf-8 -*-

import unicodedata

# ------------------------------------------------------------
# Pequeno léxico de verbos irregulares/frequentes (forma de lema simplificada)
# ------------------------------------------------------------
VERB_LEXICON = {
    "λεγω", "φερω", "ειμι", "φημι", "οιδα",
    "γιγνομαι", "τιθημι", "διδωμι", "ιημι", "ερχομαι",
    "λαμβανω", "λελοιπα", "οραω", "πασχω", "πινω",
    "πιπτω", "τικτω", "τρεχω", "τρεπω", "τασσω",
}

# Terminações típicas do presente
PRESENT_ACTIVE = ["ω", "εις", "ει", "ομεν", "ετε", "ουσιν"]
PRESENT_MIDPASS = ["ομαι", "ῃ", "ει", "εται", "ομεθα", "εσθε", "ονται"]


# ------------------------------------------------------------
# Utilidades
# ------------------------------------------------------------
def normalize(text):
    return unicodedata.normalize("NFC", (text or "").strip())


def simplify(text):
    """Remove diacríticos e baixa para minúsculas."""
    s = normalize(text)
    s = "".join(ch for ch in unicodedata.normalize("NFD", s)
                if not unicodedata.combining(ch))
    return s.lower()


# ------------------------------------------------------------
# Núcleo das heurísticas — versão B2 (segura)
# ------------------------------------------------------------
def detect_pos_and_lemma(word_simp):
    """
    Retorna (pos, lema_estimado) usando heurísticas **conservadoras**.

    Regras:
      1. Se a forma está no léxico → é verbo irregular → retorna lema exato
      2. Se termina com sufixos verbais comuns → verbo → lema + 'ω'
      3. Caso contrário → assume substantivo/adjetivo → lema = base (NÃO adiciona 'ω')
    """

    # 1) Léxico de verbos
    if word_simp in VERB_LEXICON:
        return "verbo", word_simp

    # 2) Presente ativo
    for suf in PRESENT_ACTIVE:
        if word_simp.endswith(suf):
            base = word_simp[:-len(suf)]
            if base.endswith("ω"):
                return "verbo", base
            return "verbo", base + "ω"

    # 3) Presente médio/passivo
    for suf in PRESENT_MIDPASS:
        if word_simp.endswith(suf):
            base = word_simp[:-len(suf)]
            if base.endswith("ω"):
                return "verbo", base
            return "verbo", base + "ω"

    # 4) Caso seguro: não é verbo → retorna a forma como lema
    return "substantivo/adjetivo", word_simp


# ------------------------------------------------------------
# Função principal
# ------------------------------------------------------------
def morph_analyze_simple(word):
    entrada = word
    norm = normalize(word)
    simp = simplify(word)

    pos, lema = detect_pos_and_lemma(simp)

    result = {
        "entrada": entrada,
        "normalizado": norm,
        "simplificado": simp,
        "pos": pos,
        "tempo": None,
        "modo": None,
        "voz": None,
        "pessoa": None,
        "numero": None,
        "caso": None,
        "genero": None,
        "lema": lema,
        "notas": []
    }

    # Se for verbo, tentar enriquecer
    if pos == "verbo":
        # Pessoa e número (mínimo)
        if simp.endswith("ω"):
            result["pessoa"] = "1ª"
            result["numero"] = "singular"
        elif simp.endswith("εις"):
            result["pessoa"] = "2ª"
            result["numero"] = "singular"
        elif simp.endswith("ει"):
            result["pessoa"] = "3ª"
            result["numero"] = "singular"
        elif simp.endswith("ομεν"):
            result["pessoa"] = "1ª"
            result["numero"] = "plural"
        elif simp.endswith("ετε"):
            result["pessoa"] = "2ª"
            result["numero"] = "plural"
        elif simp.endswith("ουσιν"):
            result["pessoa"] = "3ª"
            result["numero"] = "plural"

        # Modo/voz padrão
        result["modo"] = "indicative"
        result["tempo"] = "present"
        if any(simp.endswith(s) for s in PRESENT_MIDPASS):
            result["voz"] = "middle/passive"
        else:
            result["voz"] = "active"

    return result
