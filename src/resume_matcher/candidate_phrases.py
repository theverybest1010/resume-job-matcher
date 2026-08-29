import spacy
from spacy.language import Language


DEFAULT_SPACY_MODEL = "en_core_web_sm"


class CandidatePhraseExtractor:
    """Extract meaningful phrases that may describe skills."""

    def __init__(
        self,
        model_name: str = DEFAULT_SPACY_MODEL,
        max_tokens: int = 6,
        nlp: Language | None = None,
    ) -> None:
        if max_tokens < 1:
            raise ValueError("max_tokens must be at least 1.")

        self.max_tokens = max_tokens

        # A custom pipeline can be provided during testing.
        # Otherwise, load spaCy's trained English pipeline.
        if nlp is not None:
            self.nlp = nlp
        else:
            try:
                self.nlp = spacy.load(model_name)
            except OSError as error:
                raise RuntimeError(
                    f"spaCy model '{model_name}' is not installed. "
                    f"Run: python -m spacy download {model_name}"
                ) from error

    def extract(
        self,
        text: str,
    ) -> list[str]:
        """Extract unique action-oriented candidate phrases."""

        text = text.strip()

        # Empty text contains no candidate phrases.
        if not text:
            return []

        # Analyze the grammar of the complete document.
        document = self.nlp(text)

        candidates: list[str] = []
        seen_phrases: set[str] = set()

        for chunk in document.noun_chunks:
            # Prepositional objects provide context for another action,
            # so they should not become separate skill candidates.
            #
            # Examples:
            # "hospital patients"
            # "several clients"
            if chunk.root.dep_ == "pobj":
                continue

            # Start with the boundaries of the noun phrase.
            candidate_start = chunk.start
            candidate_end = chunk.end

            # Find the word grammatically controlling the noun phrase.
            governing_word = chunk.root.head

            # Include the action verb controlling the noun phrase.
            #
            # "medical care" becomes "provided medical care"
            if (
                governing_word.pos_ == "VERB"
                and governing_word.i < chunk.start
            ):
                candidate_start = governing_word.i

            # Check whether recipient context follows the noun phrase.
            #
            # Example:
            # "provided medical care to hospital patients"
            if chunk.end < len(document):
                next_word = document[chunk.end]

                # The recipient may be attached either to the noun phrase
                # or to its governing action verb.
                recipient_belongs_to_action = (
                    chunk.start
                    <= next_word.head.i
                    < chunk.end
                    or next_word.head.i == governing_word.i
                )

                # Depending on the surrounding sentence structure, spaCy
                # may classify "to" as either a dative or a preposition.
                #
                # Checking the word itself handles both grammar parses.
                has_recipient_context = (
                    next_word.dep_ == "dative"
                    or next_word.lower_ == "to"
                )

                if (
                    has_recipient_context
                    and recipient_belongs_to_action
                ):
                    recipient_subtree = list(
                        next_word.subtree
                    )

                    proposed_end = (
                        max(
                            token.i
                            for token in recipient_subtree
                        )
                        + 1
                    )

                    proposed_span = document[
                        candidate_start:proposed_end
                    ]

                    proposed_tokens = [
                        token
                        for token in proposed_span
                        if not token.is_space
                        and not token.is_punct
                    ]

                    # Include recipient context only when the complete
                    # phrase remains short enough to describe one action.
                    if len(proposed_tokens) <= self.max_tokens:
                        candidate_end = proposed_end

            # Create the final candidate phrase.
            candidate_span = document[
                candidate_start:candidate_end
            ]

            meaningful_tokens = [
                token
                for token in candidate_span
                if not token.is_space and not token.is_punct
            ]

            # Ignore empty and excessively long phrases.
            if (
                not meaningful_tokens
                or len(meaningful_tokens) > self.max_tokens
            ):
                continue

            # Every candidate must contain a noun or proper noun.
            if not any(
                token.pos_ in {"NOUN", "PROPN"}
                for token in meaningful_tokens
            ):
                continue

            phrase = candidate_span.text.strip()
            normalized_phrase = phrase.casefold()

            # Remove duplicates while preserving document order.
            if normalized_phrase not in seen_phrases:
                seen_phrases.add(normalized_phrase)
                candidates.append(phrase)

        return candidates