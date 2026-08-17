from dataclasses import dataclass

import spacy
from spacy.matcher import PhraseMatcher

from resume_matcher.skills import Skill


@dataclass(frozen=True)
class SkillMention:
    skill: Skill
    matched_text: str
    start_char: int
    end_char: int


class ExactSkillExtractor:
    def __init__(self, skills: list[Skill]) -> None:
        self._nlp = spacy.blank("en")
        self._matcher = PhraseMatcher(
            self._nlp.vocab,
            attr="LOWER",
        )
        self._skills_by_match_id: dict[int, Skill] = {}

        for skill in skills:
            labels = {
                label.strip()
                for label in skill.labels
                if label.strip()
            }

            patterns = [
                self._nlp.make_doc(label)
                for label in labels
            ]

            if not patterns:
                continue

            self._matcher.add(skill.uri, patterns)

            match_id = self._nlp.vocab.strings[skill.uri]
            self._skills_by_match_id[match_id] = skill

    def extract(self, text: str) -> list[SkillMention]:
        doc = self._nlp.make_doc(text)
        matches = self._matcher(doc)

        candidates_by_span: dict[
            tuple[int, int],
            list[SkillMention],
        ] = {}

        seen_mentions: set[tuple[str, int, int]] = set()

        for match_id, start, end in matches:
            skill = self._skills_by_match_id[match_id]
            matched_span = doc[start:end]

            mention_key = (
                skill.uri,
                matched_span.start_char,
                matched_span.end_char,
            )

            if mention_key in seen_mentions:
                continue

            seen_mentions.add(mention_key)

            mention = SkillMention(
                skill=skill,
                matched_text=matched_span.text,
                start_char=matched_span.start_char,
                end_char=matched_span.end_char,
            )

            span_key = (
                matched_span.start_char,
                matched_span.end_char,
            )

            candidates_by_span.setdefault(span_key, []).append(mention)

        resolved_mentions: list[SkillMention] = []

        for candidates in candidates_by_span.values():
            canonical_matches = [
                mention
                for mention in candidates
                if mention.matched_text.casefold()
                == mention.skill.preferred_label.casefold()
            ]

            resolved_mentions.extend(canonical_matches or candidates)

        return resolved_mentions
    