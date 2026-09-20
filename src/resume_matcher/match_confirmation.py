"""Conservative grammatical equivalence; no synonym or action substitution."""
from functools import lru_cache


class GrammaticalMatchVerifier:
    def __init__(self, nlp):
        self.nlp = nlp

    @lru_cache(maxsize=2048)
    def _signature(self, text):
        # Preserve negation, modifiers, and prepositions; ignore only a/an/the.
        # Lowercase before parsing to reduce sentence-initial capitalization effects.
        doc = self.nlp(text.strip().lower())
        tokens = [token for token in doc if not token.is_space]
        while tokens and tokens[0].text in {"•", "-", "–"}:
            tokens.pop(0)
        while tokens and tokens[-1].text in {".", ";"}:
            tokens.pop()
        if not tokens or tokens[0].pos_ != "VERB":
            return None
        if any(not token.lemma_ for token in tokens):
            return None
        return tuple(token.lemma_.casefold() for token in tokens
                     if not (token.pos_ == "DET" and token.lower_ in {"a", "an", "the"}))

    def confirms(self, phrase, preferred_label):
        signature = self._signature(phrase)
        return signature is not None and signature == self._signature(preferred_label)
