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
        # The matcher cannot work without skills to search.
        if not skills:
            raise ValueError("At least one skill is required.")

        # Keep the skills in a fixed order.
        # Each skill's position must match its embedding's position.
        self.skills = tuple(skills)

        # Load the pretrained Sentence Transformer model.
        # The model is downloaded automatically the first time it is used.
        self.model = SentenceTransformer(
            model_name,
            device=device,
        )

        # Extract only the preferred ESCO label from each Skill object.
        #
        # Example:
        # Skill(preferred_label="project management", ...)
        # becomes:
        # "project management"
        skill_names = [
            skill.preferred_label
            for skill in self.skills
        ]

        # Convert all ESCO skill names into semantic embeddings.
        #
        # THIS IS THE PART THAT CONVERTS ESCO SKILLS INTO EMBEDDINGS.
        #
        # Each skill name becomes a numerical vector representing its meaning.
        # These embeddings are created once when the matcher is initialized.
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
        # Remove unnecessary spaces from the beginning and end.
        phrase = phrase.strip()

        # An empty phrase cannot be semantically matched.
        if not phrase:
            raise ValueError("Phrase must not be empty.")

        # At least one result must be requested.
        if top_k < 1:
            raise ValueError("top_k must be at least 1.")

        # Convert the input phrase into an embedding.
        #
        # THIS IS THE PART THAT CONVERTS THE RESUME OR JOB PHRASE
        # INTO AN EMBEDDING.
        query_embedding = self.model.encode(
            [phrase],
            convert_to_tensor=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        # Compare the phrase embedding with every ESCO skill embedding.
        #
        # The search returns the ESCO skills whose meanings are closest
        # to the meaning of the input phrase.
        results = semantic_search(
            query_embedding,
            self.skill_embeddings,
            top_k=min(top_k, len(self.skills)),
        )[0]

        # Convert the raw search results into SemanticSkillMatch objects.
        #
        # corpus_id tells us which ESCO skill produced the result.
        # Results below min_score are removed.
        return [
            SemanticSkillMatch(
                skill=self.skills[int(result["corpus_id"])],
                score=float(result["score"]),
            )
            for result in results
            if float(result["score"]) >= min_score
        ]