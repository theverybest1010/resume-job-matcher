"""Load reviewed alias corrections without editing the ESCO export."""

import csv
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Literal


@dataclass(frozen=True)
class AliasRule:
    preferred_label: str
    alias: str
    action: Literal["add", "block"]
    reason: str = ""


def load_alias_rules(csv_path: str | Path | None = None) -> tuple[AliasRule, ...]:
    """Read the bundled rules, or a CSV supplied by the caller.

    A preferred label identifies an existing catalog entry. Rules never
    create a skill, change its URI, or merge related but distinct skills.
    """
    source = (
        Path(csv_path)
        if csv_path is not None
        else files("resume_matcher").joinpath("data", "alias_rules.csv")
    )
    rules: list[AliasRule] = []

    with source.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        required = {"preferredLabel", "alias", "action", "reason"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing alias-rule columns: {sorted(missing)}")

        for row in reader:
            label = (row.get("preferredLabel") or "").strip()
            alias = (row.get("alias") or "").strip()
            action = (row.get("action") or "").strip().casefold()
            if not label or not alias or action not in {"add", "block"}:
                raise ValueError(f"Invalid alias rule at CSV line {reader.line_num}.")
            rules.append(
                AliasRule(
                    preferred_label=label,
                    alias=alias,
                    action=action,
                    reason=(row.get("reason") or "").strip(),
                )
            )

    return tuple(rules)
