import os,sys,time,json,subprocess,msvcrt,traceback
from pathlib import Path
from urllib.request import urlopen
ROOT=Path(r'C:\Nexus');ON=ROOT/'ferramentas/nexus-tools/OpenNotebook'
LOG=ROOT/'registos';processes=[];streams=[]
STATUS=LOG/'open-notebook-servicos.json'
def save(state,**extra):
    STATUS.write_text(json.dumps(dict(status=state,mode='WSL sem Docker',processes=[p.pid for p in processes],**extra),indent=2),encoding='utf-8')
def ready(url):
    try:
        with urlopen(url,timeout=2) as r:return r.status==200
    except Exception:return False
def start(name,args,cwd=None,env=None):
    stream=(LOG/(name+'.log')).open('ab');streams.append(stream)
    p=subprocess.Popen([str(x) for x in args],cwd=cwd,env=env,stdout=stream,stderr=stream,creationflags=subprocess.CREATE_NO_WINDOW)
    processes.append(p);return p
def wait(url,p,timeout=150):
    until=time.monotonic()+timeout
    while time.monotonic()<until:
        if p.poll() is not None:raise RuntimeError('Servico terminou: '+url)
        if ready(url):return
        time.sleep(1)
    raise TimeoutError('Servico nao respondeu: '+url)
def main():
    with (LOG/'open-notebook-servicos.lock').open('a+b') as lock:
        try:msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        except OSError:return
        save('STARTING')
        if ready('http://127.0.0.1:8000/health') or ready('http://127.0.0.1:5055/health'):
            raise RuntimeError('Portas ocupadas fora deste supervisor; nao substituir servicos')
        env=dict(os.environ)
        env['PATH']=str(ROOT/'ferramentas/ffmpeg')+';'+str(ROOT/'ferramentas/node')+';'+env.get('PATH','')
        env['SURREAL_URL']='ws://127.0.0.1:8000/rpc'
        env['CORS_ORIGINS']='http://127.0.0.1:3000,http://localhost:3000'
        db=start('surreal-wsl',['wsl.exe','-d','Nexus','-u','root','--exec','python3','/mnt/c/Nexus/configuracao/surreal-wsl.py','8000'])
        wait('http://127.0.0.1:8000/health',db)
        api=start('open-notebook-api',[ON/'.venv/Scripts/python.exe','-m','uvicorn','api.main:app','--host','127.0.0.1','--port','5055'],ON,env)
        wait('http://127.0.0.1:5055/health',api)
        env['PYTHONUTF8']='1'
        worker=start('open-notebook-worker',[ON/'.venv/Scripts/python.exe','-X','utf8','-c','from dotenv import load_dotenv; load_dotenv(); from surreal_commands.cli.worker import main; main()','--import-modules','commands','--max-tasks','1'],ON,env)
        ui=start('open-notebook-interface',[ROOT/'ferramentas/node/node.exe',ON/'frontend/node_modules/next/dist/bin/next','start','-H','127.0.0.1','-p','3000'],ON/'frontend',env)
        wait('http://127.0.0.1:3000',ui)
        save('READY',url='http://127.0.0.1:3000',database_url=env['SURREAL_URL'])
        while all(p.poll() is None for p in processes):time.sleep(3)
        raise RuntimeError('Um servico terminou; consultar registos')
if __name__=='__main__':
    try:main()
    except Exception as e:
        save('FAIL',error=str(e))
        with (LOG/'open-notebook-supervisor.log').open('a',encoding='utf-8') as f:traceback.print_exc(file=f)
    finally:
        for p in reversed(processes):
            if p.poll() is None:p.terminate()
        for s in streams:s.close()
