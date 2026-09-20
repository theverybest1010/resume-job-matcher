from dataclasses import dataclass
from collections import defaultdict
from collections.abc import Sequence

import re

import spacy
from spacy.matcher import PhraseMatcher

from resume_matcher.alias_rules import AliasRule, load_alias_rules
from resume_matcher.skills import Skill


@dataclass(frozen=True)
class SkillMention:
    skill: Skill
    matched_text: str
    start_char: int
    end_char: int


class ExactSkillExtractor:
    def __init__(
        self,
        skills: list[Skill],
        *,
        alias_rules: Sequence[AliasRule] | None = None,
    ) -> None:
        self._nlp = spacy.blank("en")
        self._matcher = PhraseMatcher(
            self._nlp.vocab,
            attr="LOWER",
        )
        self._skills_by_match_id: dict[int, Skill] = {}

        # Keep corrections separate from the source catalog. Pass an empty
        # sequence to use the unmodified ESCO aliases for a comparison run.
        rules = load_alias_rules() if alias_rules is None else tuple(alias_rules)
        rules_by_label: dict[str, list[AliasRule]] = defaultdict(list)
        for rule in rules:
            if rule.action not in {"add", "block"}:
                raise ValueError(f"Unknown alias-rule action: {rule.action}")
            rules_by_label[rule.preferred_label.strip().casefold()].append(rule)

        # A correction must identify one concept, rather than accidentally
        # updating several distinct URIs that share a preferred label.
        uris_by_label: dict[str, set[str]] = defaultdict(set)
        for skill in skills:
            uris_by_label[skill.preferred_label.strip().casefold()].add(skill.uri)
        for label in rules_by_label:
            if len(uris_by_label[label]) > 1:
                raise ValueError(f"Alias-rule target is ambiguous: {label}")

        for skill in skills:
            # Blocks apply to this concept's aliases only. The same word
            # can still be a valid preferred label for another concept.
            relevant_rules = rules_by_label[skill.preferred_label.strip().casefold()]
            blocked = {
                rule.alias.strip().casefold()
                for rule in relevant_rules if rule.action == "block"
            }
            aliases = [*skill.aliases, *skill.contextual_aliases]
            aliases.extend(
                rule.alias for rule in relevant_rules if rule.action == "add"
            )
            labels = {skill.preferred_label.strip()}
            labels.update(
                alias.strip() for alias in aliases
                if alias.strip() and alias.strip().casefold() not in blocked
            )

            patterns = [
                self._nlp.make_doc(label)
                for label in sorted(labels)
                if label
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

            if not self._context_allows(skill, text, matched_span.start_char, matched_span.end_char):
                continue

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

            preferred = canonical_matches or candidates
            # If an alias still identifies multiple concepts, abstain.
            # Counting every interpretation would invent extra skills.
            if len(preferred) == 1:
                resolved_mentions.extend(preferred)

        return resolved_mentions

    @staticmethod
    def _context_allows(skill: Skill, text: str, start: int, end: int) -> bool:
        """Require explicit list context for short ambiguous aliases."""
        surface = text[start:end].casefold()
        ambiguous = {label.casefold() for label in skill.contextual_aliases}
        if not ambiguous:
            return True

        # A qualified alias must not start inside another language name,
        # for example the C in 'Objective-C programming'.
        prefix = text[max(0, start - 30):start]
        if re.search(r"(?:[\w]+-|objective\s+)$", prefix, re.IGNORECASE):
            return False
        if surface not in ambiguous:
            return True

        line_start = text.rfind("\n", 0, start) + 1
        line_end = text.find("\n", end)
        if line_end < 0:
            line_end = len(text)
        line = text[line_start:line_end]
        heading, separator, values = line.partition(":")
        if not separator or heading.strip().casefold() not in {
            value.casefold() for value in skill.context_headings
        }:
            return False
        values_start = line_start + len(heading) + 1
        if start < values_start:
            return False
        # Require the entire list item to equal the alias: 'vitamin C'
        # and 'Objective C' are not programming-language C.
        for item in re.finditer(r"[^,;|/]+", values):
            if values_start + item.start() <= start < values_start + item.end():
                return item.group().strip().rstrip(".").casefold() == surface
        return False
