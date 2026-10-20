import json,base64,re,hashlib
from pathlib import Path
from urllib.request import Request,urlopen
root=Path(r'C:\Nexus');config=json.loads((root/'configuracao/notebook.json').read_text(encoding='utf-8'))
auth=base64.b64encode(('nexus:'+config['database_password']).encode()).decode()
headers={'Authorization':'Basic '+auth,'Accept':'application/json','Surreal-NS':'nexus_workbench','Surreal-DB':'workbench'}
def query(sql):
    with urlopen(Request('http://127.0.0.1:8000/sql',data=sql.encode(),headers=headers),timeout=20) as response:
        result=json.load(response)
    if any(r['status']!='OK' for r in result):raise RuntimeError('Erro SQL')
    return result[0]['result']
info=query('INFO FOR DB;');tables=sorted(info.get('tables',{}));counts={}
for table in tables:
    if not re.fullmatch('[A-Za-z_][A-Za-z0-9_]*',table):raise RuntimeError('Nome tabela invalido')
    rows=query('SELECT count() FROM '+table+' GROUP ALL;')
    counts[table]=rows[0]['count'] if rows else 0
proof=json.loads((root/'registos/organizacao/open-notebook-preservacao.json').read_text())
for item in proof['database_files']:
    with Path(item['path']).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==item['sha256'],'Original alterado'
report={'status':'PASS','mode':'WSL local sem Docker','version':'2.7.0','database':'nexus_workbench/workbench','table_counts':counts,'original_hashes_unchanged':True}
(root/'registos/surreal-wsl-teste.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))

