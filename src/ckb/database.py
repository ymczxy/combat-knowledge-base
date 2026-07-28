from pathlib import Path
import json, sqlite3
from .model import Entity
SCHEMA="""
PRAGMA foreign_keys=ON;
CREATE TABLE entity(id TEXT PRIMARY KEY,entity_type TEXT NOT NULL,name_en TEXT NOT NULL,name_zh TEXT NOT NULL,domain TEXT NOT NULL,class TEXT NOT NULL,subclass TEXT,review_status TEXT NOT NULL,raw_json TEXT NOT NULL);
CREATE TABLE alias(entity_id TEXT NOT NULL,alias TEXT NOT NULL,FOREIGN KEY(entity_id) REFERENCES entity(id));
CREATE TABLE relation(source_id TEXT NOT NULL,relation_type TEXT NOT NULL,target_id TEXT NOT NULL);
CREATE INDEX idx_entity_domain ON entity(domain); CREATE INDEX idx_entity_class ON entity(class); CREATE INDEX idx_alias_alias ON alias(alias);
"""
def build_sqlite(entities:list[Entity],path:Path)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists(): path.unlink()
    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA)
        for e in entities:
            conn.execute("INSERT INTO entity VALUES (?,?,?,?,?,?,?,?,?)",(e.id,e.entity_type,e.name_en,e.name_zh,e.classification.get('domain',''),e.classification.get('class',''),e.classification.get('subclass'),e.provenance.get('review_status','unverified'),json.dumps(e.raw,ensure_ascii=False)))
            conn.executemany("INSERT INTO alias VALUES (?,?)",[(e.id,a) for a in e.aliases])
            conn.executemany("INSERT INTO relation VALUES (?,?,?)",[(e.id,str(r.get('type','')),str(r.get('target_id',''))) for r in e.relationships if r.get('target_id')])
