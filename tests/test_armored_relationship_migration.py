import unittest
from pathlib import Path

from ckb.assertions import canonical_fact_key
from ckb.graph import load_relationships
from ckb.model import load_entities
from ckb.predicates import load_predicate_registry


ROOT = Path(__file__).resolve().parents[1]

MIGRATED_ENTITY_IDS = {
    "ckb:platform:ground:t_18",
    "ckb:platform:ground:t_26",
    "ckb:platform:ground:bt_7",
    "ckb:platform:ground:t_28",
    "ckb:platform:ground:t_35",
    "ckb:platform:ground:kv_1",
    "ckb:platform:ground:t_34_model_1940",
    "ckb:platform:ground:is_2",
    "ckb:platform:ground:t_44",
    "ckb:platform:ground:t_54",
    "ckb:platform:ground:bt_2",
    "ckb:platform:ground:bt_5",
    "ckb:platform:ground:kv_2",
    "ckb:platform:ground:kv_1s",
    "ckb:platform:ground:is_1",
    "ckb:platform:ground:is_3",
    "ckb:platform:ground:t_55",
    "ckb:platform:ground:panzer_i",
    "ckb:platform:ground:panzer_ii",
    "ckb:platform:ground:panzer_iii",
    "ckb:platform:ground:panzer_iv",
    "ckb:platform:ground:tiger_i",
    "ckb:platform:ground:tiger_ii",
    "ckb:platform:ground:elefant",
    "ckb:platform:ground:panther_ausf_d",
    "ckb:platform:ground:panther_ausf_a",
    "ckb:platform:ground:panther_ausf_g",
}

MIGRATED_RELATIONSHIP_IDS = {
    "rel:bt_7:development_line_predecessor:t_34_model_1940",
    "rel:t_34_model_1940:developed_into:t_34_85",
    "rel:t_34_model_1940:development_line_predecessor:t_44",
    "rel:t_44:developed_into:t_54",
    "rel:kv_1:development_line_predecessor:is_2",
    "rel:v1_6_0_batch_03:t_18:influenced:t_26",
    "rel:v1_6_0_batch_03:t_28:contemporary:t_35",
    "rel:v1_6_0_batch_03:bt_2:developed_into:bt_5",
    "rel:v1_6_0_batch_03:bt_5:developed_into:bt_7",
    "rel:v1_6_0_batch_03:kv_2:variant_of:kv_1",
    "rel:v1_6_0_batch_03:kv_1s:variant_of:kv_1",
    "rel:v1_6_0_batch_03:kv_1s:development_line_predecessor:is_1",
    "rel:v1_6_0_batch_03:is_1:developed_into:is_2",
    "rel:v1_6_0_batch_03:is_2:development_line_predecessor:is_3",
    "rel:v1_6_0_batch_03:t_54:development_line_predecessor:t_55",
    "rel:v1_6_0_batch_03:panzer_i:development_line_predecessor:panzer_ii",
    "rel:v1_6_0_batch_03:panzer_iii:contemporary:panzer_iv",
    "rel:v1_6_0_batch_03:tiger_i:development_line_predecessor:tiger_ii",
    "rel:v1_6_0_batch_03:elefant:related_design:tiger_i",
    "rel:v1_6_0_batch_03:panther_ausf_d:variant_of:panther_tank",
    "rel:v1_6_0_batch_03:panther_ausf_a:variant_of:panther_tank",
    "rel:v1_6_0_batch_03:panther_ausf_g:variant_of:panther_tank",
    "rel:v1_6_0_batch_03:panther_ausf_d:developed_into:panther_ausf_a",
    "rel:v1_6_0_batch_03:panther_ausf_a:developed_into:panther_ausf_g",
}


class ArmoredRelationshipMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entities = load_entities(ROOT / "data" / "canonical")
        cls.relationships = load_relationships(ROOT / "data" / "relationships")
        cls.registry = load_predicate_registry(ROOT / "data" / "ontology" / "predicates.json")

    def test_migrated_entities_no_longer_store_embedded_relationships(self):
        entity_map = {entity.id: entity for entity in self.entities}
        self.assertEqual(set(entity_map) & MIGRATED_ENTITY_IDS, MIGRATED_ENTITY_IDS)
        remaining = {
            entity_id: entity_map[entity_id].relationships
            for entity_id in sorted(MIGRATED_ENTITY_IDS)
            if entity_map[entity_id].relationships
        }
        self.assertEqual(remaining, {})

    def test_all_normalized_migration_assertions_exist(self):
        relationship_map = {relationship.id: relationship for relationship in self.relationships}
        self.assertEqual(set(relationship_map) & MIGRATED_RELATIONSHIP_IDS, MIGRATED_RELATIONSHIP_IDS)

    def test_migration_represents_twenty_four_distinct_canonical_facts(self):
        selected = [
            relationship
            for relationship in self.relationships
            if relationship.id in MIGRATED_RELATIONSHIP_IDS
        ]
        fact_keys = {
            canonical_fact_key(relationship, self.registry)
            for relationship in selected
        }
        self.assertEqual(len(selected), 24)
        self.assertEqual(len(fact_keys), 24)


if __name__ == "__main__":
    unittest.main()
