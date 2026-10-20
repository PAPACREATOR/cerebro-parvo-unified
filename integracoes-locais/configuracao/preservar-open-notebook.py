from pathlib import Path
import json,os,shutil,hashlib,msvcrt,sqlite3
root=Path(r'C:\Nexus')
tools=root/'ferramentas/nexus-tools'
old=root/'dados/notebook-database'
dest=tools/'OpenNotebook-Data/surrealdb'
config=json.loads((root/'configuracao/notebook.json').read_text(encoding='utf-8'))
entries=[]
if not dest.exists():
    lock=(old/'LOCK').open('a+b')
    try:
        lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        dest.mkdir(parents=True)
        for p in old.rglob('*'):
            if p.is_symlink() or (p.is_dir() and os.path.isjunction(p)):raise RuntimeError('Ligacao inesperada na memoria')
            if not p.is_file() or p.name=='LOCK':continue
            target=dest/p.relative_to(old);target.parent.mkdir(parents=True,exist_ok=True)
            before=p.stat();shutil.copy2(p,target)
            with p.open('rb') as f:a=hashlib.file_digest(f,'sha256').hexdigest()
            with target.open('rb') as f:b=hashlib.file_digest(f,'sha256').hexdigest()
            if a!=b or p.stat().st_mtime_ns!=before.st_mtime_ns:raise RuntimeError('Memoria alterada durante copia')
            entries.append({'path':str(p),'target':str(target),'sha256':a})
    finally:lock.close()
source=root/'bancada/open-notebook/data'
data=tools/'OpenNotebook/data'
for category in ['podcasts','uploads']:
    if (source/category).exists() and not (data/category).exists():shutil.copytree(source/category,data/category)
for p in (source/'sqlite-db').glob('*.sqlite'):
    target=data/'sqlite-db'/p.name
    if target.exists():continue
    target.parent.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(p.as_uri()+'?mode=ro',uri=True) as src,sqlite3.connect(target) as dst:
        src.backup(dst)
        if dst.execute('PRAGMA quick_check').fetchone()[0]!='ok':raise RuntimeError('Checkpoint SQLite invalido')
envfile=tools/'OpenNotebook/.env'
if envfile.exists():raise RuntimeError('Configuracao nova existente; nao substituir automaticamente')
values={'SURREAL_URL':'ws://127.0.0.1:8000/rpc','SURREAL_USER':'nexus','SURREAL_PASSWORD':config['database_password'],'SURREAL_NAMESPACE':'nexus_workbench','SURREAL_DATABASE':'workbench','OPEN_NOTEBOOK_ENCRYPTION_KEY':config['encryption_key'],'OPEN_NOTEBOOK_PASSWORD':config['password'],'OPEN_NOTEBOOK_WORKER_MAX_TASKS':'1'}
envfile.write_text('\n'.join(k+'='+str(v) for k,v in values.items())+'\n',encoding='utf-8')
(root/'registos/organizacao/open-notebook-preservacao.json').write_text(json.dumps({'database_files':entries,'original_preserved':True,'encryption_key_preserved':True,'namespace_preserved':True},indent=2),encoding='utf-8')
print('Memoria, perfis, chaves e ficheiros existentes preservados; originais intactos',flush=True)
