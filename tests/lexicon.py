# -*- coding: utf-8 -*-

import pytest
import ddgp.lexicon as lx


def test_lexicon_load_minimal(tmp_path, monkeypatch):
    # Cria um pequeno léxico temporário
    fake = tmp_path / "fake_lex.json"
    fake.write_text(
        '[{"lemma": "λογος", "forms": ["λογος", "λογου"]}]',
        encoding="utf-8"
    )

    # Força o caminho a ser nosso arquivo fake
    monkeypatch.setattr(lx, "LEXICON_PATH", str(fake))
    monkeypatch.setattr(lx, "_LEXICON", None)

    lex = lx.get_lexicon()
    assert isinstance(lex, list)
    assert len(lex) == 1


def test_lookup_basic(tmp_path, monkeypatch):
    fake = tmp_path / "fake_lex.json"
    fake.write_text(
        '[{"lemma": "λογος", "forms": ["λογος", "λογου"]}]',
        encoding="utf-8"
    )

    monkeypatch.setattr(lx, "LEXICON_PATH", str(fake))
    monkeypatch.setattr(lx, "_LEXICON", None)

    res = lx.lookup_lexicon("λόγος")
    assert isinstance(res, list)
    assert len(res) >= 1
