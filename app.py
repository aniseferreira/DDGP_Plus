# app.py — DDGP Plus (base 27/11/25 + WIC)
# -*- coding: utf-8 -*-

import os
import json
import unicodedata
import re
from pathlib import Path
import streamlit as st

from ddgp.translit import transliterate_to_greek
from ddgp.formatting import format_pdesc

# ============================================================
# CONFIGURAÇÃO DA PÁGINA / LOGO / CSS
# ============================================================

LOGO_URL = "https://raw.githubusercontent.com/aniseferreira/DDGP_Plus/main/ddgp/logo.png"
LOGO_LOCAL = None

st.set_page_config(
    page_title="DDGP Plus — Morph & Dictionary",
    page_icon=LOGO_URL,
    layout="wide"
)
