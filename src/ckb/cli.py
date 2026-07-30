from argparse import ArgumentParser
from collections import Counter
from pathlib import Path
import json

from .adapters import MediaWikiAdapter, SourceHit, WikidataAdapter
from .batch_resolution import apply_constraints, resolve_cached_candidates, write_batch_bundle
from .catalog import CatalogItem, catalog_stats, load_catalog, validate_catalog
from .candidates import ambiguity_groups, build_candidates, write_candidate_bundle, write_drafts
from .database import build_sqlite
from .export import load_profile, select_entities, write_project_bundle
from .fact_lifecycle import apply_fact_decisions, build_fact_snapshot, load_fact_decisions
from .graph import KnowledgeGraph, embedded_relationships, load_relationships
from .importers import load_entity_csv, write_import_records
from .markdown import build_markdown
from .model import load_entities
from .predicates import load_predicate_registry
from .resolution import SearchCache, decide_matches, write_resolution_bundle
from .sources import load_source_registry, validate_source_registry
from .site import build_site_docs
from .temporal import build_temporal_index
from .query import related_entities, search_entities
from .validation import validate_all

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "canonical"
RELATIONSHIPS = ROOT / "data" / "relationships"
PREDICATES = ROOT / "data" / "ontology" / "predicates.json"
FACT_DECISIONS = ROOT / "data" / "governance" / "fact_decisions.json"


def _print_errors(errors: list[str]) -> int:
    for error in errors:
        print("ERROR:", error)
    return 1 if errors else 0


def _candidate_from_args(args: object):
    item = CatalogItem(
        group=str(getattr(args, "group")),
        name=str(getattr(args, "query")),
        status="researching",
        priority="P1",
        source_file="cli",
    )
    return build_candidates([item])[0]


def _load_fixture(path: Path):
    payload = json.loads(path.read_text(encoding="utf-8"))
    candidate_row = payload["candidate"]
    item = CatalogItem(
        group=str(candidate_row["group"]),
        name=str(candidate_row["name"]),
        status=str(candidate_row.get("status", "researching")),
        priority=str(candidate_row.get("priority", "P1")),
        source_file=str(path),
    )
    candidate = build_candidates([item])[0]
    hits = [SourceHit(
        source=str(row["source"]),
        external_id=str(row["external_id"]),
        label=str(row["label"]),
        description=str(row.get("description", "")),
        url=str(row.get("url", "")),
        aliases=tuple(str(value) for value in row.get("aliases", [])),
    ) for row in payload.get("hits", [])]
    return candidate, hits


def _build_graph(entities, include_embedded: bool = True) -> KnowledgeGraph:
    registry = load_predicate_registry(PREDICATES)
    relationships = load_relationships(RELATIONSHIPS)
    if include_embedded:
        relationships = [*embedded_relationships(entities), *relationships]
    return KnowledgeGraph(entities, relationships, predicate_registry=registry)


def _governance_with_decisions(graph_model: KnowledgeGraph, decisions_path: Path):
    report = graph_model.governance_report()
    ledger = load_fact_decisions(decisions_path)
    errors = ledger.validate(report)
    if not errors:
        apply_fact_decisions(report, ledger)
    return report, ledger, errors


def main() -> None:
    parser = ArgumentParser(prog="ckb")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("validate")
    sub.add_parser("stats")
    sub.add_parser("catalog-audit")
    sub.add_parser("source-audit")
    sub.add_parser("predicate-audit")

    temporal = sub.add_parser("temporal-audit")
    temporal.add_argument("--output", type=Path, default=ROOT / "exports" / "temporal" / "index.json")

    query = sub.add_parser("query")
    query.add_argument("--text")
    query.add_argument("--entity-type")
    query.add_argument("--domain")
    query.add_argument("--era")
    query.add_argument("--entity-id")
    query.add_argument("--predicate")
    query.add_argument("--direction", choices=["out", "in", "both"], default="both")
    query.add_argument("--limit", type=int, default=50)

    assertion_audit = sub.add_parser("assertion-audit")
    assertion_audit.add_argument("--output", type=Path)
    assertion_audit.add_argument("--exclude-embedded", action="store_true")
    assertion_audit.add_argument("--fail-on-conflict", action="store_true")
    assertion_audit.add_argument("--decisions", type=Path, default=FACT_DECISIONS)

    fact_snapshot = sub.add_parser("fact-snapshot")
    fact_snapshot.add_argument("--output", type=Path, default=ROOT / "exports" / "graph" / "fact-snapshot.json")
    fact_snapshot.add_argument("--exclude-embedded", action="store_true")
    fact_snapshot.add_argument("--decisions", type=Path, default=FACT_DECISIONS)

    candidates = sub.add_parser("candidates")
    candidates.add_argument("--output", type=Path, default=ROOT / "exports" / "candidates")

    drafts = sub.add_parser("drafts")
    drafts.add_argument("--output", type=Path, default=ROOT / "data" / "staging" / "catalog_drafts")

    ambiguity = sub.add_parser("ambiguity-report")
    ambiguity.add_argument("--json", action="store_true", dest="as_json")

    resolve_fixture = sub.add_parser("resolve-fixture")
    resolve_fixture.add_argument("input", type=Path)
    resolve_fixture.add_argument("--output", type=Path, default=ROOT / "exports" / "resolution")
    resolve_fixture.add_argument("--constraints", action="store_true")

    resolve_one = sub.add_parser("resolve-one")
    resolve_one.add_argument("query")
    resolve_one.add_argument("--group", required=True)
    resolve_one.add_argument("--source", choices=["wikidata", "wikipedia"], default="wikidata")
    resolve_one.add_argument("--language", default="en")
    resolve_one.add_argument("--limit", type=int, default=10)
    resolve_one.add_argument("--cache", type=Path, default=ROOT / "data" / "cache" / "search")
    resolve_one.add_argument("--refresh", action="store_true")
    resolve_one.add_argument("--output", type=Path, default=ROOT / "exports" / "resolution")
    resolve_one.add_argument("--constraints", action="store_true")

    batch = sub.add_parser("batch-resolve-cache")
    batch.add_argument("--cache", type=Path, default=ROOT / "data" / "cache" / "search")
    batch.add_argument("--source", default="wikidata")
    batch.add_argument("--language", default="en")
    batch.add_argument("--priority", choices=["P0", "P1", "P2", "P3"])
    batch.add_argument("--limit", type=int)
    batch.add_argument("--output", type=Path, default=ROOT / "exports" / "batch_resolution")

    import_csv = sub.add_parser("import-csv")
    import_csv.add_argument("input", type=Path)
    import_csv.add_argument("--output", type=Path, default=ROOT / "data" / "staging" / "manual_import.json")

    site = sub.add_parser("site")
    site.add_argument("--output", type=Path, default=ROOT / "site_docs")

    graph = sub.add_parser("graph")
    graph.add_argument("--output", type=Path, default=ROOT / "exports" / "graph" / "ckb-graph.json")
    graph.add_argument("--exclude-embedded", action="store_true")
    graph.add_argument("--allow-unknown-predicates", action="store_true")
    graph.add_argument("--decisions", type=Path, default=FACT_DECISIONS)

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
        graph_model = _build_graph(entities)
        errors += graph_model.validate()
        _, _, lifecycle_errors = _governance_with_decisions(graph_model, FACT_DECISIONS)
        errors += lifecycle_errors
        print(("OK" if not errors else "FAILED") + f": {len(entities)} entities")
        raise SystemExit(_print_errors(errors))

    if args.cmd == "stats":
        print("canonical_entities:", len(entities))
        for key, value in sorted(Counter(e.classification.get("domain", "Unknown") for e in entities).items()):
            print(f"  {key}: {value}")
        graph_model = _build_graph(entities)
        governance, ledger, errors = _governance_with_decisions(graph_model, FACT_DECISIONS)
        if errors:
            raise SystemExit(_print_errors(errors))
        print("relationship_assertions:", len(graph_model.relationships))
        print("canonical_facts:", len(governance.facts))
        print("duplicate_assertion_groups:", len(governance.duplicate_groups))
        print("relationship_conflicts:", len(governance.conflicts))
        print("promotion_candidates:", len(governance.promotion_candidates))
        print("fact_decisions:", len(ledger.decisions))
        for key, value in governance.lifecycle_counts.items():
            print(f"  lifecycle_{key}: {value}")
        print("predicates:", len(graph_model.predicate_registry.definitions) if graph_model.predicate_registry else 0)
        stats = catalog_stats(load_catalog(ROOT / "data" / "catalog"))
        print("catalog_candidates:", stats["total"])
        for key, value in stats["priorities"].items():
            print(f"  {key}: {value}")
        return

    if args.cmd == "predicate-audit":
        registry = load_predicate_registry(PREDICATES)
        errors = registry.validate()
        print(f"predicates: {len(registry.definitions)}")
        raise SystemExit(_print_errors(errors))

    if args.cmd == "temporal-audit":
        payload = build_temporal_index(entities)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        summary = payload["summary"]
        print(
            f"Temporal index: {summary['date_claim_count']} claims, "
            f"{summary['normalized_count']} normalized, "
            f"{summary['unparsed_count']} unparsed -> {args.output}"
        )
        raise SystemExit(1 if summary["unparsed_count"] else 0)

    if args.cmd == "query":
        if args.limit < 1:
            raise SystemExit("--limit must be positive")
        if args.entity_id:
            graph_model = _build_graph(entities)
            if args.entity_id not in graph_model.entities:
                raise SystemExit(f"unknown entity: {args.entity_id}")
            rows = related_entities(graph_model, args.entity_id, predicate=args.predicate, direction=args.direction)
        else:
            rows = search_entities(
                entities,
                text=args.text,
                entity_type=args.entity_type,
                domain=args.domain,
                era=args.era,
                limit=args.limit,
            )
        print(json.dumps([entity.raw for entity in rows], ensure_ascii=False, indent=2))
        return

    if args.cmd == "assertion-audit":
        graph_model = _build_graph(entities, include_embedded=not args.exclude_embedded)
        errors = graph_model.validate()
        report, ledger, lifecycle_errors = _governance_with_decisions(graph_model, args.decisions)
        errors += lifecycle_errors
        if errors:
            raise SystemExit(_print_errors(errors))
        payload = report.to_dict()
        payload["decision_ledger"] = ledger.to_dict()
        print(
            f"facts: {payload['fact_count']}; duplicate groups: {payload['duplicate_group_count']}; "
            f"conflicts: {payload['conflict_count']}; promotion candidates: {payload['promotion_candidate_count']}; "
            f"decisions: {len(ledger.decisions)}"
        )
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"Assertion governance report: {args.output}")
        if args.fail_on_conflict and report.conflicts:
            raise SystemExit(1)
        return

    if args.cmd == "fact-snapshot":
        graph_model = _build_graph(entities, include_embedded=not args.exclude_embedded)
        errors = graph_model.validate()
        report, ledger, lifecycle_errors = _governance_with_decisions(graph_model, args.decisions)
        errors += lifecycle_errors
        if errors:
            raise SystemExit(_print_errors(errors))
        payload = build_fact_snapshot(report, ledger)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Fact snapshot: {payload['snapshot_id']} ({payload['fact_count']} facts) -> {args.output}")
        return

    if args.cmd == "graph":
        graph_model = _build_graph(entities, include_embedded=not args.exclude_embedded)
        errors = graph_model.validate(strict_predicates=not args.allow_unknown_predicates)
        governance, _, lifecycle_errors = _governance_with_decisions(graph_model, args.decisions)
        errors += lifecycle_errors
        if errors:
            raise SystemExit(_print_errors(errors))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(graph_model.to_bundle(governance), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(
            f"Built graph: {len(graph_model.entities)} entities, "
            f"{len(graph_model.relationships)} assertions, {len(governance.facts)} facts -> {args.output}"
        )
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

    if args.cmd == "resolve-fixture":
        candidate, hits = _load_fixture(args.input)
        if args.constraints:
            decisions = apply_constraints(candidate, hits)
            write_batch_bundle(decisions, [], args.output)
            print(f"Resolved constrained fixture with {len(decisions)} ranked hits into {args.output}")
        else:
            decisions = decide_matches(candidate, hits)
            write_resolution_bundle(decisions, args.output)
            print(f"Resolved fixture with {len(decisions)} ranked hits into {args.output}")
        return

    if args.cmd == "resolve-one":
        candidate = _candidate_from_args(args)
        cache = SearchCache(args.cache)
        source_key = args.source if args.source == "wikidata" else f"wikipedia_{args.language}"
        hits = None if args.refresh else cache.get(source_key, args.query, args.language)
        if hits is None:
            adapter = WikidataAdapter() if args.source == "wikidata" else MediaWikiAdapter(args.language)
            hits = adapter.search(args.query, language=args.language, limit=args.limit) if args.source == "wikidata" else adapter.search(args.query, limit=args.limit)
            cache.put(source_key, args.query, hits, args.language)
        if args.constraints:
            decisions = apply_constraints(candidate, hits)
            write_batch_bundle(decisions, [], args.output)
            print(json.dumps([row.to_dict() for row in decisions], ensure_ascii=False, indent=2))
        else:
            decisions = decide_matches(candidate, hits)
            write_resolution_bundle(decisions, args.output)
            print(json.dumps([row.to_dict() for row in decisions], ensure_ascii=False, indent=2))
        return

    if args.cmd == "batch-resolve-cache":
        rows = build_candidates(load_catalog(ROOT / "data" / "catalog"))
        if args.priority:
            rows = [row for row in rows if row.priority == args.priority]
        if args.limit is not None:
            rows = rows[:args.limit]
        decisions, missing = resolve_cached_candidates(rows, SearchCache(args.cache), args.source, args.language)
        write_batch_bundle(decisions, missing, args.output)
        print(f"Resolved {len(decisions)} ranked hits; missing cache for {len(missing)} candidates")
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
