#!/usr/bin/env python3
"""Verify distributed bytes and internal counts. Does not rerun experiments."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
errors=[];count=0
for line in (ROOT/'MANIFEST.sha256').read_text().splitlines():
 expected,name=line.split('  ',1);p=ROOT/name
 if not p.is_file():errors.append('Missing: '+name)
 elif hashlib.sha256(p.read_bytes()).hexdigest()!=expected:errors.append('Changed: '+name)
 count+=1
if errors:
 print('\n'.join(errors),file=sys.stderr);sys.exit(1)
p=ROOT/'code_and_data/quantos_resumos_distintos_a_classe_produz.json'
d=json.loads(p.read_text());group=d['todas_as_operacoes'];groups=group['grupos']
assert d['n_clusters']==42
assert len(groups)==group['n_resumos_distintos']==18
assert sum(len(v) for v in groups.values())==group['n_operacoes']==21
r=json.loads((ROOT/'code_and_data/a_reducao_no_regime_implantado.json').read_text())
n=r['⭐_por_quantidade_substituta']['n_desc']
assert n['escolhas_iguais']==n['de_clusters']==r['n_clusters']==42
print(f'PASS: {count} file hashes; archived summaries are internally consistent.')
print('Archived counts: 42 clusters; 21 implementations; 18 distinct selection sets; 42/42 choices preserved by descriptor count.')
print('This checks frozen artifacts and count consistency, not new inference or independent recomputation of scientific results.')
