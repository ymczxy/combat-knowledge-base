from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
import json

from ckb.graph import KnowledgeGraph, embedded_relationships, load_relationships
from ckb.model import load_entities
from ckb.predicates import load_predicate_registry


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = ArgumentParser(description="Build and validate the CKB knowledge graph bundle")
    parser.add_argument("--entities", type=Path, default=ROOT / "data" / "canonical")
    parser.add_argument("--relationships", type=Path, default=ROOT / "data" / "relationships")
    parser.add_argument("--predicates", type=Path, default=ROOT / "data" / "ontology" / "predicates.json")
    parser.add_argument("--output", type=Path, default=ROOT / "exports" / "graph" / "ckb-graph.json")
    parser.add_argument("--exclude-embedded", action="store_true")
    parser.add_argument(
        "--allow-unknown-predicates",
        action="store_true",
        help="Permit legacy relationship predicates that are not yet registered.",
    )
    args = parser.parse_args()

    entities = load_entities(args.entities)
    relationships = load_relationships(args.relationships)
    registry = load_predicate_registry(args.predicates)
    if not args.exclude_embedded:
        relationships = [*embedded_relationships(entities), *relationships]

    graph = KnowledgeGraph(entities, relationships, predicate_registry=registry)
    errors = graph.validate(strict_predicates=not args.allow_unknown_predicates)
    if errors:
        for error in errors:
            print("ERROR:", error)
        raise SystemExit(1)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(graph.to_bundle(), ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"Built graph: {len(graph.entities)} entities, "
        f"{len(graph.relationships)} relationships, "
        f"{len(registry.definitions)} predicates -> {args.output}"
    )


if __name__ == "__main__":
    main()
