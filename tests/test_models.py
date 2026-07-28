import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from ckb.model import load_entities
from ckb.validation import validate_all
ROOT=Path(__file__).resolve().parents[1]
class Tests(unittest.TestCase):
    def test_seed_entities_validate(self):
        entities=load_entities(ROOT/'data'/'canonical'); self.assertGreaterEqual(len(entities),10); self.assertEqual(validate_all(entities),[])
    def test_ids_unique(self):
        ids=[e.id for e in load_entities(ROOT/'data'/'canonical')]; self.assertEqual(len(ids),len(set(ids)))
if __name__=='__main__': unittest.main()
