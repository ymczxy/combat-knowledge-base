from argparse import ArgumentParser
from collections import Counter
from pathlib import Path
import json
from .model import load_entities
from .validation import validate_all
from .database import build_sqlite
from .markdown import build_markdown
ROOT=Path(__file__).resolve().parents[2]; DATA=ROOT/'data'/'canonical'

def main():
    p=ArgumentParser(prog='ckb'); sub=p.add_subparsers(dest='cmd',required=True)
    sub.add_parser('validate'); sub.add_parser('stats'); b=sub.add_parser('build'); b.add_argument('--output',type=Path,default=ROOT/'exports')
    a=p.parse_args(); entities=load_entities(DATA)
    if a.cmd=='validate':
        errors=validate_all(entities)
        for x in errors: print('ERROR:',x)
        print(('OK' if not errors else 'FAILED')+f': {len(entities)} entities')
        raise SystemExit(1 if errors else 0)
    if a.cmd=='stats':
        print('entities:',len(entities))
        for k,v in sorted(Counter(e.classification.get('domain','Unknown') for e in entities).items()): print(f'  {k}: {v}')
        return
    errors=validate_all(entities)
    if errors:
        for x in errors: print('ERROR:',x)
        raise SystemExit(1)
    a.output.mkdir(parents=True,exist_ok=True); build_sqlite(entities,a.output/'ckb.sqlite'); build_markdown(entities,a.output/'markdown')
    (a.output/'ckb.json').write_text(json.dumps([e.raw for e in entities],ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Built {len(entities)} entities into {a.output}')

if __name__=='__main__': main()
