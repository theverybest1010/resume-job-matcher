from collections.abc import Sequence
from dataclasses import dataclass

from sentence_transformers import SentenceTransformer
from sentence_transformers.util import semantic_search

from resume_matcher.skills import Skill


# Small pretrained model used to convert text into semantic embeddings.
DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


# Represents one semantic search result.
@dataclass(frozen=True)
class SemanticSkillMatch:
    # The ESCO skill that matched the input phrase.
    skill: Skill

    # Cosine similarity between the phrase and the ESCO skill.
    score: float


class SemanticSkillMatcher:
    def __init__(
        self,
        skills: Sequence[Skill],
        model_name: str = DEFAULT_MODEL_NAME,
        device: str = "cpu",
    ) -> None:
        if not skills:
            raise ValueError("At least one skill is required.")

        # Keep skills in a fixed order so every skill continues to
        # correspond to the correct embedding.
        self.skills = tuple(skills)

        # Load the pretrained embedding model.
        self.model = SentenceTransformer(
            model_name,
            device=device,
        )

        skill_names = [
            skill.preferred_label
            for skill in self.skills
        ]

        # Convert all ESCO preferred skill labels into embeddings.
        # This happens once when the matcher is initialized.
        self.skill_embeddings = self.model.encode(
            skill_names,
            convert_to_tensor=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

    def match(
        self,
        phrase: str,
        top_k: int = 5,
        min_score: float = 0.5,
    ) -> list[SemanticSkillMatch]:
        """Match one phrase against the ESCO skills."""

        # Use the batch method internally so matching behavior remains
        # consistent for both single and multiple phrases.
        return self.match_many(
            phrases=[phrase],
            top_k=top_k,
            min_score=min_score,
        )[0]

    def match_many(
        self,
        phrases: Sequence[str],
        top_k: int = 5,
        min_score: float = 0.5,
    ) -> list[list[SemanticSkillMatch]]:
        """Match multiple phrases in one efficient model batch."""

        if top_k < 1:
            raise ValueError("top_k must be at least 1.")

        if not -1.0 <= min_score <= 1.0:
            raise ValueError(
                "min_score must be between -1.0 and 1.0."
            )

        cleaned_phrases = [
            phrase.strip()
            for phrase in phrases
        ]

        # An empty collection has no phrases to match.
        if not cleaned_phrases:
            return []

        # Individual blank phrases are likely caller mistakes.
        if any(not phrase for phrase in cleaned_phrases):
            raise ValueError("Phrases must not be empty.")

        # Convert every candidate phrase into an embedding in one batch.
        #
        # THIS IS THE PART THAT CONVERTS ALL DOCUMENT CANDIDATES
        # INTO EMBEDDINGS AT ONCE.
        query_embeddings = self.model.encode(
            cleaned_phrases,
            convert_to_tensor=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        # Compare every candidate embedding with every ESCO skill embedding.
        search_results = semantic_search(
            query_embeddings,
            self.skill_embeddings,
            top_k=min(top_k, len(self.skills)),
        )

        # Convert each candidate's raw results into useful match objects.
        return [
            [
                SemanticSkillMatch(
                    skill=self.skills[int(result["corpus_id"])],
                    score=float(result["score"]),
                )
                for result in phrase_results
                if float(result["score"]) >= min_score
            ]
            for phrase_results in search_results
        ]