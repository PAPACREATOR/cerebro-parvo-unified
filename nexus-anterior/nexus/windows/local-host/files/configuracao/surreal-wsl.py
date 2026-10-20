import os,json,hashlib,shutil,sys
from pathlib import Path
root=Path('/mnt/c/Nexus')
source=root/'ferramentas/nexus-tools/OpenNotebook-Data/surrealdb'
destination=Path('/var/lib/nexus/surrealdb')
marker=Path('/var/lib/nexus/importacao-verificada.json')
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
if not marker.exists():
    if destination.exists():raise RuntimeError('Destino existente sem prova; nao substituir')
    destination.mkdir(parents=True)
    entries=[]
    for p in source.rglob('*'):
        if p.is_symlink():raise RuntimeError('Ligacao inesperada')
        if not p.is_file() or p.name=='LOCK':continue
        target=destination/p.relative_to(source);target.parent.mkdir(parents=True,exist_ok=True)
        before=digest(p);shutil.copy2(p,target)
        if digest(target)!=before or digest(p)!=before:raise RuntimeError('Copia inconsistente')
        entries.append(dict(path=str(p.relative_to(source)),sha256=before))
    proof=dict(version='2.7.0',files=entries,original_preserved=True)
    marker.write_text(json.dumps(proof,indent=2))
    (root/'registos/organizacao/surreal-wsl-importacao.json').write_text(json.dumps(proof,indent=2))
config=json.loads((root/'configuracao/notebook.json').read_text(encoding='utf-8'))
os.environ['SURREAL_USER']='nexus'
os.environ['SURREAL_PASS']=config['database_password']
exe=str(root/'ferramentas/surreal-linux/surreal')
port=sys.argv[1] if len(sys.argv)>1 else '8000'
if port not in ('8000','18000'):raise RuntimeError('Porta inesperada')
os.execv(exe,[exe,'start','--bind','127.0.0.1:'+port,'--log','warn','rocksdb:'+str(destination)])
