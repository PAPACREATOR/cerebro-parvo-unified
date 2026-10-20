"""Validate preserved bytes and links in current documentation, without product claims."""
from pathlib import Path
import hashlib,json,re,sys
ROOT=Path(__file__).resolve().parents[1]
errors=[]
manifest=json.loads((ROOT/'auditoria/manifesto-preservacao.json').read_text())
for item in manifest:
    path=ROOT/item['path']
    if not path.is_file():
        errors.append('Missing preserved file: '+item['path'])
    elif hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:
        errors.append('Preserved bytes changed: '+item['path'])
active=list(ROOT.glob('*.md'))+list((ROOT/'docs').glob('*.md'))+list((ROOT/'tasks').glob('*.md'))+list((ROOT/'auditoria').glob('*.md'))+[ROOT/'implementacao/README.md']
links=0
for path in active:
    for target in re.findall(r'\]\(([^)]+)\)',path.read_text()):
        if target.startswith(('http:','https:','#','mailto:')):continue
        target=target.split('#')[0]
        if not target:continue
        links+=1
        resolved=(path.parent/target).resolve()
        if not resolved.is_relative_to(ROOT) or not resolved.exists():
            errors.append(str(path.relative_to(ROOT))+': unresolved local link '+target)
state=json.loads((ROOT/'auditoria/estado.json').read_text())
evidence=ROOT/state['provided_suite']['evidence']
if not evidence.is_file():errors.append('Suite evidence missing')
if state['product_release']!='NOT_APPROVED':
    errors.append('This reconciliation must not promote the product release')
# Check tracked sources and instructions cannot silently revert to the old baseline.
for p in ['README.md','AGENTS.md','CEREBRO_CONSTITUTION.md','STATUS.md','docs/MATRIZ-CONFORMIDADE.md']:
    if 'M1' not in (ROOT/p).read_text():errors.append('Missing architecture reference: '+p)
if errors:
    print('\n'.join(errors));sys.exit(1)
print(f'PASS documental: {len(manifest)} ficheiros preservados, {links} ligações locais ativas válidas.')
print('Esta verificação não atribui PASS a IMP nem aprova uma release.')
