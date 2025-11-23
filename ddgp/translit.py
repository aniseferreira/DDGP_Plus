# ddgp/translit.py
# -*- coding: utf-8 -*-
"""
Transliteração ASCII -> Grego (básica)
"""
import re

def latin_to_basic_grc(s: str) -> str:
    """Transliteração ASCII básica -> grego sem acentos (hipatia-style)."""
    if not s:
        return s
    
    # Remove dígitos (conforme regra original)
    s = "".join(ch for ch in s if not ch.isdigit())
    
    table = {
        "a":"α","b":"β","g":"γ","d":"δ",
        "e":"ε","z":"ζ","h":"η","q":"θ",
        "i":"ι","k":"κ","l":"λ","m":"μ",
        "n":"ν","c":"ξ","o":"ο","p":"π",
        "r":"ρ","s":"σ","t":"τ","u":"υ",
        "f":"φ","x":"χ","y":"ψ","w":"ω",
        "v":"β", # Adicionado 'v' para flexibilidade, se necessário
    }
    
    out = []
    prev = ""
    for ch in s.lower(): # Garante que a entrada é tratada como minúscula
        # Trata espaços para produzir sigma final ς quando apropriado
        if ch == " " and prev == "σ":
            out[-1] = "ς"
            out.append(" ")
            prev = " "
            continue
        
        gr = table.get(ch, ch)
        out.append(gr)
        prev = gr
        
    # Trata sigma final (no fim da palavra)
    if out and out[-1] == "σ":
        out[-1] = "ς"
        
    return "".join(out)

# Função de importação que o app.py espera
transliterate_to_greek = latin_to_basic_grc