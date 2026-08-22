from dataclasses import dataclass
from typing import Literal

from resume_matcher.candidate_phrases import CandidatePhraseExtractor
from resume_matcher.semantic_matcher import SemanticSkillMatcher
from resume_matcher.skill_extractor import ExactSkillExtractor
from resume_matcher.skills import Skill


# Identifies whether a skill was found through exact or semantic matching.
MatchSource = Literal["exact", "semantic"]


@dataclass(frozen=True)
class HybridSkillMention:
    # The canonical ESCO skill.
    skill: Skill

    # The original phrase that caused the match.
    matched_text: str

    # Whether the match was exact or semantic.
    source: MatchSource

    # Exact matches receive 1.0.
    # Semantic matches receive their cosine similarity score.
    score: float


class HybridSkillExtractor:
    """Combine exact ESCO extraction with semantic skill matching."""

    def __init__(
        self,
        exact_extractor: ExactSkillExtractor,
        candidate_extractor: CandidatePhraseExtractor,
        semantic_matcher: SemanticSkillMatcher,
        min_semantic_score: float = 0.75,
    ) -> None:
        if not 0.0 <= min_semantic_score <= 1.0:
            raise ValueError(
                "min_semantic_score must be between 0.0 and 1.0."
            )

        self.exact_extractor = exact_extractor
        self.candidate_extractor = candidate_extractor
        self.semantic_matcher = semantic_matcher
        self.min_semantic_score = min_semantic_score

    def extract(
        self,
        text: str,
    ) -> list[HybridSkillMention]:
        """Extract canonical skills using exact and semantic methods."""

        results: list[HybridSkillMention] = []
        seen_skill_uris: set[str] = set()

        # STEP 1: Find explicit ESCO labels and aliases.
        #
        # Exact matches have the highest precision, so they are processed
        # before semantic matches.
        exact_mentions = self.exact_extractor.extract(text)

        for mention in exact_mentions:
            skill_uri = mention.skill.uri

            # Count each canonical ESCO skill only once.
            if skill_uri in seen_skill_uris:
                continue

            seen_skill_uris.add(skill_uri)

            results.append(
                HybridSkillMention(
                    skill=mention.skill,
                    matched_text=mention.matched_text,
                    source="exact",
                    score=1.0,
                )
            )

        # STEP 2: Find meaningful phrases that exact matching may have missed.
        candidate_phrases = self.candidate_extractor.extract(text)

        # STEP 3: Match all candidate phrases semantically in one batch.
        semantic_results = self.semantic_matcher.match_many(
            candidate_phrases,
            top_k=1,
            min_score=self.min_semantic_score,
        )

        # Each candidate phrase corresponds to one semantic result list.
        for phrase, phrase_matches in zip(
            candidate_phrases,
            semantic_results,
            strict=True,
        ):
            # No ESCO skill passed the semantic threshold.
            if not phrase_matches:
                continue

            best_match = phrase_matches[0]
            skill_uri = best_match.skill.uri

            # Exact matches take priority.
            # Also prevent duplicate semantic skills.
            if skill_uri in seen_skill_uris:
                continue

            seen_skill_uris.add(skill_uri)

            results.append(
                HybridSkillMention(
                    skill=best_match.skill,
                    matched_text=phrase,
                    source="semantic",
                    score=best_match.score,
                )
            )

        return results