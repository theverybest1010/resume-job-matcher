"""Combine unchanged ESCO data with reviewed project-owned concepts."""
import csv
from dataclasses import replace
from importlib.resources import files
from pathlib import Path

from resume_matcher.skills import Skill, load_esco_skills


def load_skill_catalog(
    esco_path: str | Path,
    supplemental_path: str | Path | None = None,
) -> list[Skill]:
    """Load both catalogs. Custom supplements replace the bundled supplement."""
    skills = load_esco_skills(esco_path)
    source = (Path(supplemental_path) if supplemental_path is not None else
              files("resume_matcher").joinpath("data/supplemental_skills.csv"))
    seen = {skill.uri for skill in skills}
    additions = []
    transfers = []
    required = {"uri", "preferredLabel", "aliases", "skillType",
                "contextualAliases", "contextHeadings", "semanticMatching",
                "replacesAliasFrom", "replacesAlias", "reason"}
    with source.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing supplemental columns: {sorted(missing)}")
        for row in reader:
            if any(row[key] is None for key in required):
                raise ValueError("Incomplete supplemental skill row.")
            uri, label = row["uri"].strip(), row["preferredLabel"].strip()
            if not uri.startswith("urn:resume-job-matcher:skill:") or not label:
                raise ValueError("Supplemental skills need a project URI and label.")
            if uri in seen:
                raise ValueError(f"Duplicate skill URI: {uri}")
            seen.add(uri)
            semantic = row["semanticMatching"].strip().casefold()
            if semantic not in {"true", "false"}:
                raise ValueError("semanticMatching must be true or false.")
            def parts(key):
                return tuple(dict.fromkeys(x.strip() for x in row[key].split("|") if x.strip()))
            contexts, headings = parts("contextualAliases"), parts("contextHeadings")
            if contexts and (not headings or semantic != "false"):
                raise ValueError("Contextual aliases need headings and semanticMatching=false.")
            skill = Skill(uri, label, parts("aliases"), row["skillType"].strip(),
                          contexts, headings, semantic == "true")
            additions.append(skill)
            parent, alias = row["replacesAliasFrom"].strip(), row["replacesAlias"].strip()
            if bool(parent) != bool(alias):
                raise ValueError("Alias transfers need both a source URI and alias.")
            if parent:
                if alias.casefold() not in {x.casefold() for x in skill.labels}:
                    raise ValueError("Transferred alias must belong to the new skill.")
                transfers.append((parent, alias.casefold()))

    # Move only explicitly reviewed aliases from broader concepts. This changes
    # in-memory objects, never the source CSV; canonical ESCO labels stay intact.
    for parent, alias in transfers:
        skills = [replace(skill, aliases=tuple(
            value for value in skill.aliases if value.casefold() != alias
        )) if skill.uri == parent else skill for skill in skills]
    return [*skills, *additions]
