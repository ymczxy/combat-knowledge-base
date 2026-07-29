from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ckb.catalog import load_catalog
from ckb.candidates import build_candidates
from ckb.promotion import build_proposals, write_promotion_bundle


def main() -> None:
    parser = ArgumentParser(description="Build reviewable canonical promotion proposals from batch decisions")
    parser.add_argument("decisions", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "exports" / "promotion")
    args = parser.parse_args()
    payload = json.loads(args.decisions.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise SystemExit("decisions file must contain a JSON array")
    candidates = build_candidates(load_catalog(ROOT / "data" / "catalog"))
    proposals = build_proposals(candidates, payload)
    write_promotion_bundle(proposals, args.output)
    print(f"Built {len(proposals)} canonical promotion proposals into {args.output}")


if __name__ == "__main__":
    main()
