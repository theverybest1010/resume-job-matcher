import csv
from dataclasses import dataclass
from pathlib import Path

#these are the columns in esco csv, our loader depends on this
REQUIRED_COLUMNS = {
    "conceptUri",
    "preferredLabel",
    "altLabels",
    "skillType",
}

@dataclass(frozen=True)
class Skill:
    uri: str
    preferred_label: str
    aliases: tuple[str, ...] #alternate names for the skills
    skill_type: str

    # Ambiguous aliases require a labeled list; excluded skills need exact evidence.
    contextual_aliases: tuple[str, ...] = ()
    context_headings: tuple[str, ...] = ()
    allow_semantic_matching: bool = True

    @property
    def labels(self) -> tuple[str, ...]:
        return (self.preferred_label, *self.aliases, *self.contextual_aliases) #combines official label and aliases and returns it as tuple


#this is our loaders to load the skills from esco csv, returns list of SKILLS object 
def load_esco_skills(csv_path: str | Path) -> list[Skill]:
    skills: list[Skill] = []
    seen_uris: set[str] = set()

    with Path(csv_path).open(
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        missing_columns = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing_columns:
            raise ValueError(
                f"Missing required ESCO columns: {sorted(missing_columns)}"
            )

        for row in reader:
            uri = row["conceptUri"].strip()
            preferred_label = row["preferredLabel"].strip()

            if not uri or not preferred_label or uri in seen_uris:
                continue

            seen_uris.add(uri)

            aliases = tuple(
                alias.strip()
                for alias in row["altLabels"].splitlines()
                if alias.strip()
            )

            skills.append(
                Skill(
                    uri=uri,
                    preferred_label=preferred_label,
                    aliases=aliases,
                    skill_type=row["skillType"].strip(),
                )
            )

    return skills
