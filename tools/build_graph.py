from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
import json

from ckb.graph import KnowledgeGraph, embedded_relationships, load_relationships
from ckb.model import load_entities


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = ArgumentParser(description="Build and validate the CKB knowledge graph bundle")
    parser.add_argument("--entities", type=Path, default=ROOT / "data" / "canonical")
    parser.add_argument("--relationships", type=Path, default=ROOT / "data" / "relationships")
    parser.add_argument("--output", type=Path, default=ROOT / "exports" / "graph" / "ckb-graph.json")
    parser.add_argument("--exclude-embedded", action="store_true")
    args = parser.parse_args()

    entities = load_entities(args.entities)
    relationships = load_relationships(args.relationships)
    if not args.exclude_embedded:
        relationships = [*embedded_relationships(entities), *relationships]

    graph = KnowledgeGraph(entities, relationships)
    errors = graph.validate()
    if errors:
        for error in errors:
            print("ERROR:", error)
        raise SystemExit(1)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(graph.to_bundle(), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Built graph: {len(graph.entities)} entities, {len(graph.relationships)} relationships -> {args.output}")


if __name__ == "__main__":
    main()
