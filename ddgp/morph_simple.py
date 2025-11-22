# morph_simple.py — Heuristic ancient Greek morphological analyzer (Option A)
# - Opção A: strip diacritics before analysis (compatível com simplify() used in app.py)
# - Returns a dict with fields: entrada, normalizado, simplificado, pos, tempo, modo, voz,
#   pessoa, numero, caso, genero, lema, notas
#
# This is a heuristic analyzer: prioritized ending-rules, person/number mapping and lemma derivation.
# It is intended as an improved drop-in replacement for the smaller morph_simple used earlier.

import unicodedata
import re

def normalize(text):
    return unicodedata.normalize("NFC", (text or "")).strip()

def strip_diacritics(text):
    """Remove combining diacritics (NFD -> strip -> NFC)."""
    if not text:
        return text
    s = unicodedata.normalize("NFD", text)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return unicodedata.normalize("NFC", s)

def simplify(text):
    """Normalize and remove diacritics; lowercase. Matches the app's simplify strategy."""
    s = strip_diacritics(normalize(text or ""))
    return "".join(ch for ch in unicodedata.normalize("NFD", s) if not unicodedata.combining(ch)).lower()

# PRIORITIZED ENDING RULES (regex tails) -> feature fragments.
# Longer/rarer endings must come first.
ENDING_RULES = [
    # PARTICIPLE forms (present/perfect etc.) — simplified match
    (r'(ων|ουσα|ον)$', {'pos':'participle'}),
    # INFINITIVE (ειν, σαι, σθαι...)
    (r'(ειν|σθαι|σθαι)$', {'pos':'infinitive','modo':'infinitive'}),
    # AORIST ACTIVE (first aorist) endings: σα, σας, σε, σαμεν, σατε, σαν
    (r'(σαμεν|σατε|σαν|σας|σε|σα)$', {'tempo':'aorist','modo':'indicative','voz':'active'}),
    # AORIST PASSIVE (θην forms)
    (r'(θημεν|θητε|θησαν|θην|θης|θη)$', {'tempo':'aorist','modo':'indicative','voz':'passive'}),
    # PERFECT-like heuristic (κα, κεν etc.)
    (r'(κεν|κας|κα|κε)$', {'tempo':'perfect','modo':'indicative'}),
    # IMPERFECT typical endings (ον,ες,ε(ν),ομεν,ετε)
    (r'(ομεν|ετε|ον|ες|ενα)$', {'tempo':'imperfect','modo':'indicative'}),
    # FUTURE endings (σω,σει,σομεν,σετε)
    (r'(σομεν|σετε|σει|σω|σουσιν|σουσι)$', {'tempo':'future','modo':'indicative'}),
    # PRESENT active indicative endings
    (r'(ομεν|ετε|ουσιν|ουσι|εις|ει|ω)$', {'tempo':'present','modo':'indicative','voz':'active'}),
    # PRESENT middle/passive endings
    (r'(μαι|σαι|ται|μεθα|σθε|νται)$', {'tempo':'present','modo':'indicative','voz':'middle/passive'}),
    # OPTATIVE endings (οιμι, οις, οι, οιμεν, οιτε) — simplified
    (r'(οιμην|οιμεν|οιτε|οις|οι|οιαν)$', {'modo':'optative'}),
    # Imperative (short forms) — heuristic
    (r'(ε|ετε)$', {'modo':'imperative'}),
    # fallback small endings: 'ει' etc.
    (r'(ει)$', {'tempo':'present','modo':'indicative'}),
]

# PERSON/NUMBER mapping heuristics for common endings (present paradigm + some middle ones)
PERSON_NUMBER = {
    'ω': ('1ª','singular'),
    'εις': ('2ª','singular'),
    'ει': ('3ª','singular'),
    'ομεν': ('1ª','plural'),
    'ετε': ('2ª','plural'),
    'ουσιν': ('3ª','plural'),
    'ουσι': ('3ª','plural'),
    'μαι': ('1ª','singular'),
    'σαι': ('2ª','singular'),
    'ται': ('3ª','singular'),
    'μεθα': ('1ª','plural'),
    'σθε': ('2ª','plural'),
    'νται': ('3ª','plural'),
    'ον': ('?','plural_or_3sg'),  # ambiguous in some paradigms
    'ες': ('2ª','singular'),
}

def match_ending(s):
    """Return pattern and feature fragment that matches s (first match in priority order)."""
    for pattern, feat in ENDING_RULES:
        if re.search(pattern + r'$', s):
            return (pattern, feat.copy())
    return (None, {})

def extract_person_number(s):
    """Return pessoa/numero from PERSON_NUMBER heuristics (longest-first)."""
    for ending in sorted(PERSON_NUMBER.keys(), key=lambda x: -len(x)):
        if s.endswith(ending):
            val = PERSON_NUMBER[ending]
            if isinstance(val, tuple) and len(val) == 2:
                return {'pessoa': val[0], 'numero': val[1]}
    return {'pessoa': None, 'numero': None}

def derive_lema_from_stem(s, matched_pattern):
    """
    Heuristic lemma derivation:
    - if we matched an ending, strip it and append 'ω' (present 1sg thematic) to create a lemma.
    - if no match, return s (fallback).
    """
    base = s
    if matched_pattern:
        m = re.search(matched_pattern + r'$', s)
        if m:
            base = s[:m.start()]
    if not base:
        return s
    # If base ends with consonant cluster that likely needs vowel insertion, don't attempt fancy repairs.
    return base + 'ω'

def morph_analyze_simple(word):
    """
    Main analyzer function.
    Input: word (may contain diacritics). We will normalize and strip diacritics.
    Output: dict with morphological features.
    """
    entrada = word or ""
    normalizado = normalize(entrada)
    simpl = simplify(entrada)

    out = {
        "entrada": entrada,
        "normalizado": normalizado,
        "simplificado": simpl,
        "pos": None,
        "tempo": None,
        "modo": None,
        "voz": None,
        "pessoa": None,
        "numero": None,
        "caso": None,
        "genero": None,
        "lema": None,
        "notas": []
    }

    if not simpl:
        out['pos'] = 'unknown'
        out['notas'].append('empty-after-simplify')
        return out

    # match prioritized endings
    matched_pattern, feats = match_ending(simpl)

    # fill fields from feats
    for k,v in feats.items():
        out[k] = v

    # person/number heuristics
    pn = extract_person_number(simpl)
    out['pessoa'] = pn.get('pessoa')
    out['numero'] = pn.get('numero')

    # voice heuristics using typical endings
    if re.search(r'(μαι|σαι|ται|σθε|νται)$', simpl):
        if not out.get('voz'):
            out['voz'] = 'middle/passive'

    # pos heuristics for infinitive/participle
    if not out.get('pos'):
        if re.search(r'(ειν|σθαι)$', simpl):
            out['pos'] = 'infinitive'
            out['modo'] = 'infinitive'
        elif re.search(r'(ων|ουσα|ον)$', simpl):
            out['pos'] = 'participle'
        else:
            out['pos'] = 'verbo'

    # If tempo not set but word ends with present endings, mark present (simple heuristic)
    if not out.get('tempo') and re.search(r'(ω|εις|ει|ομεν|ετε|ουσιn|ουσι|ουσιν)$', simpl):
        out['tempo'] = out.get('tempo') or 'present'

    # Leammatization attempt
    try:
        lema = derive_lema_from_stem(simpl, matched_pattern)
        out['lema'] = lema
    except Exception as e:
        out['lema'] = simpl
        out['notas'].append('lemma-derive-error:' + str(e))

    # If pessoa/numero missing but verb, add note
    if out.get('pessoa') is None and out.get('pos') == 'verbo':
        out['notas'].append('fallback-person-detection')

    # Normalize empties to None for clarity
    for k in ['tempo','modo','voz','pessoa','numero','caso','genero']:
        if out.get(k) is None:
            out[k] = None

    return out

# Quick demo run if executed as script (not imported)
if __name__ == "__main__":
    tests = ["λεγουσιν", "λεγω", "λεξω", "ελεγον", "φερω", "πεπυκα", "λυω", "λυομεν", "λυσειν", "λαβον"]
    for t in tests:
        print(t, "->", morph_analyze_simple(t))

