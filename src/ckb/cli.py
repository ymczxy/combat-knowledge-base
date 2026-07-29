from argparse import ArgumentParser
from collections import Counter
from pathlib import Path
import json

from .catalog import catalog_stats, load_catalog, validate_catalog
from .candidates import ambiguity_groups, build_candidates, write_candidate_bundle, write_drafts
from .database import build_sqlite
from .export import load_profile, select_entities, write_project_bundle
from .importers import load_entity_csv, write_import_records
from .markdown import build_markdown
from .model import load_entities
from .sources import load_source_registry, validate_source_registry
from .site import build_site_docs
from .validation import validate_all

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "canonical"


def _print_errors(errors: list[str]) -> int:
    for error in errors:
        print("ERROR:", error)
    return 1 if errors else 0


def main() -> None:
    parser = ArgumentParser(prog="ckb")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("validate")
    sub.add_parser("stats")
    sub.add_parser("catalog-audit")
    sub.add_parser("source-audit")

    candidates = sub.add_parser("candidates")
    candidates.add_argument("--output", type=Path, default=ROOT / "exports" / "candidates")

    drafts = sub.add_parser("drafts")
    drafts.add_argument("--output", type=Path, default=ROOT / "data" / "staging" / "catalog_drafts")

    ambiguity = sub.add_parser("ambiguity-report")
    ambiguity.add_argument("--json", action="store_true", dest="as_json")

    import_csv = sub.add_parser("import-csv")
    import_csv.add_argument("input", type=Path)
    import_csv.add_argument("--output", type=Path, default=ROOT / "data" / "staging" / "manual_import.json")

    site = sub.add_parser("site")
    site.add_argument("--output", type=Path, default=ROOT / "site_docs")

    build = sub.add_parser("build")
    build.add_argument("--output", type=Path, default=ROOT / "exports")
    build.add_argument("--profile", type=str)
    build.add_argument("--allow-unverified", action="store_true")
    args = parser.parse_args()

    entities = load_entities(DATA)

    if args.cmd == "validate":
        errors = validate_all(entities)
        errors += validate_catalog(load_catalog(ROOT / "data" / "catalog"))
        errors += validate_source_registry(load_source_registry(ROOT / "sources" / "registry.json"))
        print(("OK" if not errors else "FAILED") + f": {len(entities)} entities")
        raise SystemExit(_print_errors(errors))

    if args.cmd == "stats":
        print("canonical_entities:", len(entities))
        for key, value in sorted(Counter(e.classification.get("domain", "Unknown") for e in entities).items()):
            print(f"  {key}: {value}")
        stats = catalog_stats(load_catalog(ROOT / "data" / "catalog"))
        print("catalog_candidates:", stats["total"])
        for key, value in stats["priorities"].items():
            print(f"  {key}: {value}")
        return

    if args.cmd == "catalog-audit":
        items = load_catalog(ROOT / "data" / "catalog")
        errors = validate_catalog(items)
        print(json.dumps(catalog_stats(items), ensure_ascii=False, indent=2))
        raise SystemExit(_print_errors(errors))

    if args.cmd in {"candidates", "drafts", "ambiguity-report"}:
        rows = build_candidates(load_catalog(ROOT / "data" / "catalog"))
        if args.cmd == "candidates":
            write_candidate_bundle(rows, args.output)
            print(f"Built {len(rows)} candidates into {args.output}")
            print(f"Ambiguity keys: {len(ambiguity_groups(rows))}")
            return
        if args.cmd == "drafts":
            write_drafts(rows, args.output)
            print(f"Built {len(rows)} reviewable drafts into {args.output}")
            return
        groups = ambiguity_groups(rows)
        if args.as_json:
            print(json.dumps({key: [row.to_dict() for row in value] for key, value in groups.items()}, ensure_ascii=False, indent=2))
        else:
            for key, value in groups.items():
                print(f"[{key}]")
                for row in value:
                    print(f"  - {row.source_name} ({row.source_group}) -> {row.candidate_id}")
        return

    if args.cmd == "import-csv":
        rows = load_entity_csv(args.input)
        write_import_records(rows, args.output)
        print(f"Imported {len(rows)} rows into {args.output}")
        return

    if args.cmd == "site":
        catalog = load_catalog(ROOT / "data" / "catalog")
        errors = validate_all(entities) + validate_catalog(catalog)
        if errors:
            raise SystemExit(_print_errors(errors))
        build_site_docs(entities, catalog, ROOT, args.output)
        print(f"Built site source into {args.output}")
        return

    if args.cmd == "source-audit":
        rows = load_source_registry(ROOT / "sources" / "registry.json")
        errors = validate_source_registry(rows)
        print(f"sources: {len(rows)}")
        raise SystemExit(_print_errors(errors))

    errors = validate_all(entities)
    if errors:
        raise SystemExit(_print_errors(errors))
    args.output.mkdir(parents=True, exist_ok=True)
    build_sqlite(entities, args.output / "ckb.sqlite")
    build_markdown(entities, args.output / "markdown")
    (args.output / "ckb.json").write_text(
        json.dumps([e.raw for e in entities], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if args.profile:
        profile_path = ROOT / "data" / "curated" / args.profile / "build_profile.json"
        profile = load_profile(profile_path)
        selected = select_entities(entities, profile, allow_unverified=args.allow_unverified)
        path = write_project_bundle(selected, profile, args.output)
        print(f"Project bundle: {path} ({len(selected)} entities)")
    print(f"Built {len(entities)} entities into {args.output}")


if __name__ == "__main__":
    main()
