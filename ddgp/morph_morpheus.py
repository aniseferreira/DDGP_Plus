# ddgp/morph_morpheus.py
# -*- coding: utf-8 -*-
"""
HuggingFace-based optional morphology analyzer for Ancient Greek (parallel mode).
MODO 1 — HF is optional and runs in parallel to morph_simple.py. It never replaces
the deterministic fallback nor touches the DDGP indices.
Public API:
    - morph_hf_available() -> bool
    - morph_hf_analyze(word: str) -> dict | None
The returned dict follows the same skeleton as morph_simple.morph_analyze_simple:
{
 "entrada","normalizado","simplificado",
 "pos","tempo","voz","pessoa","numero","caso","genero","lema","notas":[...]
}
If HF models are not installed or an error occurs, morph_hf_analyze returns None.
Configuration:
 - Set environment variables or edit LOCAL_MODEL_NAMES to point to desired HF models.
 - By default, the module will attempt to load:
     * a seq2seq lemmatizer model name from MORPH_HF_LEMMATIZER env var
     * a token-classification / POS model from MORPH_HF_TAGGER env var
     * fallback tagger name: "pranaydeeps/Ancient-Greek-BERT" (encoder-only; used as feature extractor)
"""
import os, unicodedata, re, logging
from typing import Optional

LOG = logging.getLogger("morph_morpheus")
LOG.addHandler(logging.NullHandler())

# minimal normalization utilities (same style as morph_simple)
def normalize(t: str) -> str:
    return unicodedata.normalize("NFC", (t or "")).strip()

def strip_diacritics(t: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFD", (t or "")) if not unicodedata.combining(ch))

def simplify(t: str) -> str:
    return strip_diacritics(normalize(t)).lower()

# Config: model names (can be overridden by environment)
SEQ2SEQ_MODEL = os.environ.get("MORPH_HF_LEMMATIZER")  # e.g. "your-user/ancient-greek-t5-lemma"
TAGGER_MODEL = os.environ.get("MORPH_HF_TAGGER", "pranaydeeps/Ancient-Greek-BERT")
# NOTE: pranaydeeps/Ancient-Greek-BERT is encoder-only; it can be used as feature extractor
# If you have a token-classification or seq2seq checkpoint for lemmatization/tagging,
# set the environment variables above.

# lazy imports and model holders
_HF_AVAILABLE = False
_seq2seq = None
_seq2seq_tokenizer = None
_tagger = None
_tagger_tokenizer = None
_torch = None

# attempt to load transformers components if available
try:
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, AutoModel, AutoModelForTokenClassification, pipeline
    import torch
    _torch = torch
    # try seq2seq lemmatizer if specified
    if SEQ2SEQ_MODEL:
        try:
            _seq2seq_tokenizer = AutoTokenizer.from_pretrained(SEQ2SEQ_MODEL)
            _seq2seq = AutoModelForSeq2SeqLM.from_pretrained(SEQ2SEQ_MODEL)
            LOG.info("Loaded seq2seq lemmatizer: %s", SEQ2SEQ_MODEL)
            _HF_AVAILABLE = True
        except Exception as e:
            LOG.warning("Could not load seq2seq lemmatizer %s: %s", SEQ2SEQ_MODEL, e)
            _seq2seq = None
            _seq2seq_tokenizer = None
    # try tagger/token-classification
    try:
        # Try to load a token-classification model first
        _tagger_tokenizer = AutoTokenizer.from_pretrained(TAGGER_MODEL)
        # attempt to load token classification; if fails, load generic encoder
        try:
            _tagger = AutoModelForTokenClassification.from_pretrained(TAGGER_MODEL)
            LOG.info("Loaded token-classification model: %s", TAGGER_MODEL)
            _HF_AVAILABLE = True
        except Exception:
            # fallback: load encoder-only model (feature extractor)
            try:
                _tagger = AutoModel.from_pretrained(TAGGER_MODEL)
                LOG.info("Loaded encoder model (feature extractor): %s", TAGGER_MODEL)
                _HF_AVAILABLE = True
            except Exception as e:
                LOG.warning("Could not load tagger/encoder model %s: %s", TAGGER_MODEL, e)
                _tagger = None
                _tagger_tokenizer = None
    except Exception as e:
        LOG.warning("Could not load tokenizer for tagger model %s: %s", TAGGER_MODEL, e)
        _tagger = None
        _tagger_tokenizer = None

except Exception as e:
    LOG.info("transformers/torch not available or failed to import: %s", e)
    _HF_AVAILABLE = False

def morph_hf_available() -> bool:
    """Signal whether any HF model loaded successfully."""
    return bool(_HF_AVAILABLE)

# helper to format output skeleton
def _skeleton(word: str):
    w = normalize(word)
    s = simplify(w)
    return {
        "entrada": word,
        "normalizado": w,
        "simplificado": s,
        "pos": None, "tempo": None, "voz": None,
        "pessoa": None, "numero": None,
        "caso": None, "genero": None,
        "lema": None, "notas": []
    }

def _map_tokenclass_preds(preds):
    """
    Convert typical token-classification predictions (labels) into coarse POS/features.
    preds: list of dicts from pipeline(token-classification) or raw logits.
    Returns a small dict with keys like pos, number, person, tense, voice, case, gender.
    """
    features = {"pos": None, "tense": None, "voice": None, "person": None, "number": None, "case": None, "gender": None}
    # heuristics: look for common tags in label names
    for p in preds:
        label = (p.get("entity") or p.get("label") or "").lower()
        # generic heuristics
        if "verb" in label or label.startswith("v"):
            features["pos"] = "verbo"
        if "noun" in label or label.startswith("n"):
            features["pos"] = "substantivo"
        if "adj" in label or "adj" in label:
            features["pos"] = "adjetivo"
        if "aor" in label or "aorist" in label:
            features["tense"] = "aoristo"
        if "pres" in label or "present" in label:
            features["tense"] = "presente"
        if "perf" in label or "perfect" in label:
            features["tense"] = "perfeito"
        if "pass" in label:
            features["voice"] = "passiva"
        if "mid" in label or "med" in label:
            features["voice"] = "média"
        if "1" in label and "sg" in label:
            features["person"] = "1ª"; features["number"] = "singular"
        if "2" in label and "sg" in label:
            features["person"] = "2ª"; features["number"] = "singular"
        if "3" in label and "sg" in label:
            features["person"] = "3ª"; features["number"] = "singular"
        if "pl" in label:
            features["number"] = "plural"
        if "nom" in label:
            features["case"] = "nominativo"
        if "gen" in label:
            features["case"] = "genitivo"
        if "dat" in label:
            features["case"] = "dativo"
        if "acc" in label:
            features["case"] = "acusativo"
        if "masc" in label:
            features["gender"] = "masculino"
        if "fem" in label:
            features["gender"] = "feminino"
        if "neut" in label:
            features["gender"] = "neutro"
    return features

def _seq2seq_lemmatize(word: str) -> Optional[str]:
    """Generate lemma using seq2seq model if available."""
    if not _seq2seq or not _seq2seq_tokenizer:
        return None
    try:
        # Prepare simple input: can be expanded to include context
        inp = word
        enc = _seq2seq_tokenizer(inp, return_tensors="pt")
        if _torch and _torch.cuda.is_available():
            device = "cuda"
        else:
            device = _seq2seq.device if hasattr(_seq2seq, "device") else "cpu"
        _seq2seq.to(device)
        for k,v in enc.items():
            if hasattr(v, "to"):
                try:
                    enc[k] = v.to(device)
                except Exception:
                    pass
        out = _seq2seq.generate(**enc, max_length=32)
        lemma = _seq2seq_tokenizer.decode(out[0], skip_special_tokens=True)
        if lemma:
            return strip_diacritics(lemma)
    except Exception as e:
        LOG.warning("seq2seq lemmatize failed: %s", e)
    return None

def _tag_with_tagger(word: str):
    """Try a token-classification pipeline if a token-classification model is loaded."""
    if not _tagger or not _tagger_tokenizer:
        return None
    try:
        # If we have a pipeline-capable token-classification model, use pipeline
        try:
            nlp = None
            # if AutoModelForTokenClassification was loaded, try pipeline
            from transformers import pipeline
            nlp = pipeline("token-classification", model=_tagger, tokenizer=_tagger_tokenizer, aggregation_strategy="simple")
            preds = nlp(word)
            return preds
        except Exception:
            # if we only have encoder (AutoModel), we can't produce labels; return None
            return None
    except Exception as e:
        LOG.warning("tagger failed: %s", e)
        return None

def morph_hf_analyze(word: str) -> Optional[dict]:
    """
    Main entrypoint. Returns a dict compatible with morph_simple.morph_analyze_simple,
    or None if HF models are not available or analysis failed.
    """
    if not morph_hf_available():
        return None
    sk = _skeleton(word)
    try:
        # 1) lemma: prefer seq2seq if available
        lemma = None
        if _seq2seq:
            lemma = _seq2seq_lemmatize(word)
            if lemma:
                sk["lema"] = lemma
                sk["notas"].append("hf_seq2seq")
        # 2) tagging/features: try tagger
        preds = None
        if _tagger:
            preds = _tag_with_tagger(word)
        # if no tagger output but we have encoder-only, try to use heuristics (not implemented here)
        if preds:
            feats = _map_tokenclass_preds(preds)
            # map features into skeleton (coarse)
            sk["pos"] = feats.get("pos") or sk["pos"]
            sk["tempo"] = feats.get("tense") or sk["tempo"]
            sk["voz"] = feats.get("voice") or sk["voz"]
            # person/number mapping to expected labels
            if feats.get("person"):
                sk["pessoa"] = feats.get("person")
            if feats.get("number"):
                sk["numero"] = feats.get("number")
            if feats.get("case"):
                sk["caso"] = feats.get("case")
            if feats.get("gender"):
                sk["genero"] = feats.get("gender")
            sk["notas"].append("hf_tagger")
        # 3) if we have no lemma but seq2seq absent, try to use tagger output to guess lemma (not ideal)
        if not sk.get("lema"):
            # try a simple heuristic: strip common endings (very conservative)
            s = simplify(word)
            # remove common verb endings if present
            for ending in ("εις","ει","ου","ον","εν","εις","ε","εις","ες"):
                if s.endswith(ending):
                    sk["lema"] = strip_diacritics(s[:-len(ending)]) + "ω"
                    sk["notas"].append("hf_heuristic_verb")
                    break
        # finalize fields
        sk["normalizado"] = normalize(word)
        sk["simplificado"] = simplify(sk["normalizado"])
        if not sk.get("lema"):
            # If still no lemma, return None to let deterministic fallback run
            return None
        return sk
    except Exception as e:
        LOG.warning("morph_hf_analyze failed: %s", e)
        return None
