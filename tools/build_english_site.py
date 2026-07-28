from __future__ import annotations

from argparse import ArgumentParser
from collections import defaultdict
from pathlib import Path
from typing import Any
import json
import shutil

from ckb.catalog import CatalogItem, load_catalog
from ckb.model import Entity, load_entities

ROOT = Path(__file__).resolve().parents[1]
SITE_ROOT = "https://ymczxy.github.io/combat-knowledge-base"


def slug(value: str) -> str:
    return value.replace(":", "__").replace("/", "_").replace(" ", "_").lower()


def entity_file(entity: Entity) -> str:
    return slug(entity.id) + ".md"


def front_matter(title: str, description: str = "") -> str:
    lines = ["---", f"title: {json.dumps(title, ensure_ascii=False)}"]
    if description:
        lines.append(f"description: {json.dumps(description, ensure_ascii=False)}")
    lines.extend(["---", ""])
    return "\n".join(lines)


def language_note() -> str:
    return f"[:material-translate: 简体中文]({SITE_ROOT}/){{ .md-button }}\n"


def display(value: Any) -> str:
    if value is None or value == "":
        return "Not recorded"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, (list, tuple)):
        return ", ".join(display(item) for item in value) if value else "Not recorded"
    if isinstance(value, dict):
        return f"`{json.dumps(value, ensure_ascii=False)}`"
    return str(value)


def escape_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def json_section(title: str, value: Any, note: str | None = None) -> list[str]:
    lines = [f"## {title}", ""]
    if note:
        lines.extend([f"> {note}", ""])
    if value:
        lines.extend(["```json", json.dumps(value, ensure_ascii=False, indent=2), "```", ""])
    else:
        lines.extend(["Not available yet.", ""])
    return lines


def render_entity(entity: Entity) -> str:
    classification = entity.classification
    provenance = entity.provenance
    title = entity.name_en or entity.name_zh
    aliases = ", ".join(entity.aliases) or "Not recorded"
    lines = [
        front_matter(title, f"CKB entity page for {title}"),
        language_note(),
        f"# {title}",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| CKB ID | `{entity.id}` |",
        f"| English name | {escape_cell(entity.name_en or 'Not recorded')} |",
        f"| Chinese name | {escape_cell(entity.name_zh or 'Not recorded')} |",
        f"| Aliases | {escape_cell(aliases)} |",
        f"| Entity type | {escape_cell(entity.entity_type)} |",
        f"| Domain | {escape_cell(display(classification.get('domain')))} |",
        f"| Class | {escape_cell(display(classification.get('class')))} |",
        f"| Subclass | {escape_cell(display(classification.get('subclass')))} |",
        f"| Eras | {escape_cell(display(classification.get('eras', [])))} |",
        f"| Tags | {escape_cell(display(classification.get('tags', [])))} |",
        f"| Review status | {escape_cell(display(provenance.get('review_status')))} |",
        "",
    ]
    lines.extend(json_section("Technical data", entity.technical))
    lines.extend(json_section(
        "Experience profile",
        entity.experience_profile,
        "These values are perceptible gameplay abstractions, not direct real-world test measurements.",
    ))
    lines.extend(json_section("Gameplay configuration", entity.gameplay))
    lines.extend(["## Entity relationships", ""])
    if entity.relationships:
        lines.extend(["| Relationship | Target |", "|---|---|"])
        for relation in entity.relationships:
            target = str(relation.get("target_id", ""))
            target_link = f"[{target}]({slug(target)}.md)" if target else "Not recorded"
            lines.append(f"| {relation.get('type', 'related')} | {target_link} |")
    else:
        lines.append("No relationships have been recorded.")
    lines.extend(["", "## Sources", ""])
    sources = provenance.get("sources", [])
    if sources:
        for source in sources:
            if isinstance(source, dict):
                label = source.get("name") or source.get("source_id") or "Source"
                url = source.get("url")
                lines.append(f"- [{label}]({url})" if url else f"- {label}")
            else:
                lines.append(f"- {source}")
    else:
        lines.append("No sources have been registered.")
    lines.extend([
        "",
        "## Raw structured data",
        "",
        "??? note \"Expand JSON\"",
        "",
        "    ```json",
    ])
    raw = json.dumps(entity.raw, ensure_ascii=False, indent=2)
    lines.extend(f"    {line}" for line in raw.splitlines())
    lines.extend(["    ```", "", "> Generated automatically by CKB. Do not edit this page directly.", ""])
    return "\n".join(lines)


def write_home(output: Path, entities: list[Entity], catalog: list[CatalogItem]) -> None:
    domains = {str(entity.classification.get("domain", "Unknown")) for entity in entities}
    eras = {str(era) for entity in entities for era in entity.classification.get("eras", [])}
    lines = [
        front_matter("Combat Knowledge Base", "English browser for the Combat Knowledge Base"),
        language_note(),
        "# Combat Knowledge Base",
        "",
        "CKB normalizes dispersed information about weapons, ammunition, platforms, materials, sensors and environments into searchable entities, while producing game-ready data for *destory*.",
        "",
        "<div class=\"grid cards\" markdown>",
        "",
        f"-   :material-database: **{len(entities)} canonical entities**",
        "",
        "    [Browse entities →](entities/index.md)",
        "",
        f"-   :material-format-list-bulleted: **{len(catalog)} catalog candidates**",
        "",
        "    [Browse the full catalog →](catalog/index.md)",
        "",
        f"-   :material-shape: **{len(domains)} implemented domains**",
        "",
        "    [Browse by domain →](browse/domains/index.md)",
        "",
        f"-   :material-timeline-clock: **{len(eras)} implemented eras**",
        "",
        "    [Browse by era →](browse/eras/index.md)",
        "",
        "</div>",
        "",
        "!!! warning \"Knowledge base under construction\"",
        "    Catalog candidates are not verified entities. Only records under `data/canonical` belong to the canonical dataset.",
        "",
        "## Quick links",
        "",
        "- [Architecture](reference/ARCHITECTURE.md)",
        "- [Data standard](reference/DATA_STANDARD.md)",
        "- [Modern equipment experience model](reference/MODERN_EXPERIENCE_MODEL.md)",
        "- [Godot integration](reference/GODOT_INTEGRATION.md)",
        "- [Source strategy](reference/SOURCE_STRATEGY.md)",
        "- [Roadmap](reference/ROADMAP.md)",
        "- [Decisions](reference/DECISIONS.md)",
        "",
    ]
    (output / "index.md").write_text("\n".join(lines), encoding="utf-8")


def write_entities(output: Path, entities: list[Entity]) -> None:
    root = output / "entities"
    root.mkdir(parents=True, exist_ok=True)
    grouped: dict[str, list[Entity]] = defaultdict(list)
    for entity in entities:
        grouped[str(entity.classification.get("domain", "Unknown"))].append(entity)
        (root / entity_file(entity)).write_text(render_entity(entity), encoding="utf-8")
    lines = [front_matter("Canonical entities"), language_note(), "# Canonical entities", ""]
    for domain in sorted(grouped):
        lines.extend([f"## {domain}", "", "| English name | Chinese name | Class | Eras | Status |", "|---|---|---|---|---|"])
        for entity in sorted(grouped[domain], key=lambda item: item.name_en.casefold()):
            cls = " / ".join(part for part in [entity.classification.get("class"), entity.classification.get("subclass")] if part)
            eras = ", ".join(entity.classification.get("eras", []))
            status = str(entity.provenance.get("review_status", ""))
            lines.append(f"| [{entity.name_en}]({entity_file(entity)}) | {entity.name_zh} | {cls} | {eras} | {status} |")
        lines.append("")
    (root / "index.md").write_text("\n".join(lines), encoding="utf-8")


def write_browse(output: Path, entities: list[Entity]) -> None:
    domain_root = output / "browse" / "domains"
    era_root = output / "browse" / "eras"
    domain_root.mkdir(parents=True, exist_ok=True)
    era_root.mkdir(parents=True, exist_ok=True)

    domains: dict[str, list[Entity]] = defaultdict(list)
    eras: dict[str, list[Entity]] = defaultdict(list)
    for entity in entities:
        domains[str(entity.classification.get("domain", "Unknown"))].append(entity)
        for era in entity.classification.get("eras", []):
            eras[str(era)].append(entity)

    domain_lines = [front_matter("Browse by domain"), language_note(), "# Browse by domain", ""]
    for domain in sorted(domains):
        domain_lines.extend([f"## {domain}", ""])
        for entity in sorted(domains[domain], key=lambda item: item.name_en.casefold()):
            domain_lines.append(f"- [{entity.name_en}](../../entities/{entity_file(entity)}) — {entity.name_zh}")
        domain_lines.append("")
    (domain_root / "index.md").write_text("\n".join(domain_lines), encoding="utf-8")

    era_lines = [front_matter("Browse by era"), language_note(), "# Browse by era", ""]
    for era in sorted(eras):
        era_lines.extend([f"## {era}", ""])
        for entity in sorted(eras[era], key=lambda item: item.name_en.casefold()):
            era_lines.append(f"- [{entity.name_en}](../../entities/{entity_file(entity)}) — {entity.name_zh}")
        era_lines.append("")
    (era_root / "index.md").write_text("\n".join(era_lines), encoding="utf-8")


def write_catalog(output: Path, catalog: list[CatalogItem]) -> None:
    root = output / "catalog"
    root.mkdir(parents=True, exist_ok=True)
    grouped: dict[str, list[CatalogItem]] = defaultdict(list)
    for item in catalog:
        grouped[item.group].append(item)
    lines = [
        front_matter("Full construction catalog"),
        language_note(),
        "# Full construction catalog",
        "",
        f"There are currently **{len(catalog)}** candidates. This is a research queue, not the canonical dataset.",
        "",
    ]
    for group in sorted(grouped):
        lines.extend([f"## {group}", "", "| Name | Status | Priority |", "|---|---|---|"])
        for item in sorted(grouped[group], key=lambda row: (row.priority, row.name.casefold())):
            lines.append(f"| {escape_cell(item.name)} | {item.status} | {item.priority} |")
        lines.append("")
    (root / "index.md").write_text("\n".join(lines), encoding="utf-8")


REFERENCE_PAGES = {
    "ARCHITECTURE.md": ("Architecture", "CKB separates source claims, canonical entities, experience profiles and project-specific game data. JSON is the canonical source format; Markdown, SQLite and Godot bundles are generated outputs."),
    "DATA_STANDARD.md": ("Data standard", "Every entity has a stable CKB ID, bilingual identity fields, classification, provenance, relationships and optional technical, experience and gameplay layers. Real-world facts and game-derived values must remain separate."),
    "MODERN_EXPERIENCE_MODEL.md": ("Modern equipment experience model", "Modern systems are described through nine perceptible dimensions: acoustics, visuals, impulse, handling, environmental effects, target response, sensor UX, crew burden, and failure or degradation cues."),
    "GODOT_INTEGRATION.md": ("Godot integration", "Godot consumes a version-locked project subset rather than the full knowledge base. Encyclopedia data, simulation profiles, balance data and presentation resources are exported as separate layers."),
    "SOURCE_STRATEGY.md": ("Source strategy", "CKB combines official publications, museums, structured knowledge graphs, specialist archives and open datasets. Each field should retain provenance, qualifiers and confidence instead of hiding conflicting claims."),
    "ROADMAP.md": ("Roadmap", "The roadmap progresses from engineering and taxonomy, through source adapters and historical coverage, to modern experience profiles, deep *destory* integration and long-tail maintenance."),
    "DECISIONS.md": ("Architecture decisions", "CKB is an independent repository. Chinese is the default website language, English is served under `/en/`, and modern equipment remains limited to public knowledge and safe gameplay abstraction."),
}


def write_references(output: Path) -> None:
    root = output / "reference"
    root.mkdir(parents=True, exist_ok=True)
    for filename, (title, body) in REFERENCE_PAGES.items():
        text = "\n".join([front_matter(title), language_note(), f"# {title}", "", body, ""])
        (root / filename).write_text(text, encoding="utf-8")


def build(output: Path) -> None:
    entities = load_entities(ROOT / "data" / "canonical")
    catalog = load_catalog(ROOT / "data" / "catalog")
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)
    write_home(output, entities, catalog)
    write_entities(output, entities)
    write_browse(output, entities)
    write_catalog(output, catalog)
    write_references(output)
    print(f"Built English site source: {len(entities)} entities, {len(catalog)} catalog candidates")


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "site_docs_en")
    args = parser.parse_args()
    build(args.output)


if __name__ == "__main__":
    main()
