from collections import Counter
from .model import Entity
VALID_REVIEW={"planned","unverified","machine_imported","source_checked","cross_checked","expert_reviewed","deprecated"}

def validate_entity(e: Entity) -> list[str]:
    errors=[]
    if not e.id.startswith("ckb:"): errors.append(f"{e.id}: invalid id prefix")
    if not e.name_en: errors.append(f"{e.id}: missing canonical_name_en")
    if not e.name_zh: errors.append(f"{e.id}: missing canonical_name_zh")
    if not e.classification.get("domain"): errors.append(f"{e.id}: missing domain")
    if not e.classification.get("class"): errors.append(f"{e.id}: missing class")
    if e.provenance.get("review_status") not in VALID_REVIEW: errors.append(f"{e.id}: invalid review_status")
    return errors

def validate_all(entities: list[Entity]) -> list[str]:
    errors=[]
    for e in entities: errors.extend(validate_entity(e))
    counts=Counter(e.id for e in entities)
    errors += [f"{k}: duplicate id ({v})" for k,v in counts.items() if v>1]
    known=set(counts)
    for e in entities:
        for rel in e.relationships:
            target=rel.get("target_id")
            if target and target not in known: errors.append(f"{e.id}: missing relationship target {target}")
    return errors
