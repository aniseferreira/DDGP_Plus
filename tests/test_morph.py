# -*- coding: utf-8 -*-

import pytest
from ddgp.morph import analyze_word

def test_analyze_word_basic():
    result = analyze_word("λόγος")

    assert isinstance(result, dict)
    assert "normalized" in result
    assert "lemma_guess" in result
    assert "pos_guess" in result

def test_analyze_empty():
    assert analyze_word("") == {}
    assert analyze_word("   ") == {}
