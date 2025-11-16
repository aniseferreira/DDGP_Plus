# ddgp/morph.py — Comprehensive paradigm-based analyzer (Option B)
# -*- coding: utf-8 -*-
"""
Comprehensive morphological analyzer for DDGP Plus (Option B)

Design:
- Loads paradigm JSONs from ddgp/data/morph/
- Matches longest possible endings (priority by length)
- Recognizes: present, imperfect, future (thematic/sigmatic), aorist I (sigmatic), aorist passive, perfect, participles
- Handles middle/passive/active, person and number, and reconstructs a candidate lemma (stem + ω)
- Uses irregular_verbs.json for supletive/lema overrides
- Returns a dict with keys: input, normalized, simplified, pos, tense, mood, voice, person, number, lemma, notes
"""
import os, json, unicodedata, re

BASE_DIR = os.path.dirname(__file__)
MORPH_DATA_DIR = os.path.join(BASE_DIR, "data", "morph")

def _load_json(filename):
    path = os.path.join(MORPH_DATA_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing morph data file: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# Load paradigm files
PRES_A = _load_json("endings_present_active.json")
PRES_M = _load_json("endings_present_middle.json")
IMP_A = _load_json("endings_imperfect_active.json")
FUT_A = _load_json("endings_future_active.json")
FUT_M = _load_json("endings_future_middle.json")
FUT_P = _load_json("endings_future_passive.json")
A1_A = _load_json("endings_aorist1_active.json")
A1_M = _load_json("endings_aorist1_middle.json")
A1_P = _load_json("endings_aorist1_passive.json")
PERF_A = _load_json("endings_perfect_active.json")
PERF_M = _load_json("endings_perfect_middle.json")
PARTS = _load_json("participles.json")
IRREG = _load_json("irregular_verbs.json")

# Utilities
def normalize(text: str) -> str:
    return unicodedata.normalize("NFC", text or "").strip()

def strip_diacritics(text: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFD", text or "") if not unicodedata.combining(ch))

def simplify(text: str) -> str:
    return strip_diacritics(normalize(text)).lower()

# Match endings (longest-first) across one or more dicts
def match_endings(simplified_form: str, *ending_dicts):
    candidates = []
    for ed in ending_dicts:
        for ending in sorted(ed.keys(), key=len, reverse=True):
            end_s = simplify(ending)
            if simplified_form.endswith(end_s):
                info = dict(ed[ending]) if isinstance(ed[ending], dict) else {"code": ed[ending]}
                info["_ending"] = ending
                info["_ending_s"] = end_s
                candidates.append(info)
    # return candidates ordered by matched ending length descending
    candidates.sort(key=lambda c: len(c.get("_ending_s", "")), reverse=True)
    return candidates

# Reconstruct lemma: naive stem + ω; will be refined with irregular list or by lexicon lookup
def reconstruct_lemma_from_stem(simplified_stem: str):
    # return with combining removed, add final omega (lowercase)
    stem = strip_diacritics(simplified_stem)
    # simple heuristics for contraction: if stem ends with vowel, keep as-is; lemma = stem + 'ω'
    return stem + "ω"

# Main analysis function
def morph_analyze(word: str):
    w = normalize(word)
    s = simplify(w)
    result = {
        "input": word,
        "normalized": w,
        "simplified": s,
        "pos": None,
        "tense": None,
        "mood": None,
        "voice": None,
        "person": None,
        "number": None,
        "lemma": None,
        "notes": []
    }

    if not s:
        return result

    # 0. irregular lookup: if simplified form starts with irregular lemma key, use it
    for key, info in IRREG.items():
        if s.startswith(simplify(key)):
            # IRREG may map to a lemma or contain tags
            lemma = info.get("lemma") if isinstance(info, dict) else info
            result.update({"pos":"verb", "lemma":lemma})
            result["notes"].append(f"irregular_match:{key}")
            return result

    # 1. participles (try first — participles often have distinct endings)
    part_cands = match_endings(s, PARTS)
    if part_cands:
        best = part_cands[0]
        result["pos"] = "participle"
        result["tense"] = best.get("tense")
        result["voice"] = best.get("voice")
        result["gender"] = best.get("gender")
        result["number"] = best.get("number")
        result["case"] = best.get("case")
        result["notes"].append(f"participle_end:{best.get('_ending')}")
        # lemma heuristic: remove ending and add ω
        stem_s = s[:-len(best.get("_ending_s"))] if best.get("_ending_s") else s
        result["lemma"] = reconstruct_lemma_from_stem(stem_s)
        return result

    # 2. priority paradigms list (order matters)
    paradigms = [
        (FUT_M, "future"),
        (FUT_A, "future"),
        (FUT_P, "future"),
        (A1_A, "aorist"),
        (A1_M, "aorist"),
        (A1_P, "aorist"),
        (PERF_M, "perfect"),
        (PERF_A, "perfect"),
        (IMP_A, "imperfect"),
        (PRES_M, "present"),
        (PRES_A, "present"),
    ]

    for pd, pd_tense in paradigms:
        cands = match_endings(s, pd)
        if cands:
            best = cands[0]
            # set basic fields
            result["pos"] = "verb"
            result["tense"] = best.get("tense", pd_tense)
            result["voice"] = best.get("voice")
            # person and number if present in mapping
            if "person" in best:
                result["person"] = best.get("person")
            if "number" in best:
                result["number"] = best.get("number")
            # sometimes the dict stores labels like '1sg_fut_act' — try to parse them
            codevals = best.get("code") or ""
            # parse person/number from codes like '1sg' or '1pl' if available
            m = re.search(r'([123])\s*pl|([123])\s*sg', codevals)
            # fallback parse for patterns
            # compute lemma candidate by removing matched ending from simplified form
            stem_s = s[:-len(best.get("_ending_s"))] if best.get("_ending_s") else s
            lemma_candidate = reconstruct_lemma_from_stem(stem_s)
            result["lemma"] = lemma_candidate
            result["notes"].append(f"ending_matched:{best.get('_ending')}")
            return result

    # 3. fallback: if string contains Greek letters, propose simplified as lemma
    if re.search(r'[\u0370-\u03FF\u1F00-\u1FFF]', s):
        result["lemma"] = strip_diacritics(s)
        result["notes"].append("fallback_lemma_from_form")
    return result

# module test if run as script
if __name__ == "__main__":
    tests = ["βουλεύσομεν","βουλεύσομαι","εἶπον","λέγω","ἔλυσα","λέγουσι","λελυκως","ἀγαπῶ","ἤγαγον"]
    for t in tests:
        print(t, "->", morph_analyze(t))
