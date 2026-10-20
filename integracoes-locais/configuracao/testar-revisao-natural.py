"""A single real, confined LanguageTool execution via a natural request."""
from pathlib import Path
import argparse, json, base64, hashlib, sys, threading, time, shutil
from contextlib import contextmanager
from urllib.request import Request, urlopen
from urllib.error import HTTPError

p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--data-test',type=Path,required=True);p.add_argument('--config',type=Path,default=Path(r'C:\Nexus\dados\languagetool.json'));p.add_argument('--report',type=Path,required=True)
args=p.parse_args();repo=args.repo.resolve();data=args.data_test.resolve()
assert not data.exists() and not data.is_relative_to(Path(r'C:\Nexus\dados').resolve())
assert not data.is_relative_to(repo)
data.mkdir(parents=True)
shutil.copyfile(args.config,data/'languagetool.json')
sys.path.insert(0,str(repo))
from nexus.app import application
import nexus.host as host_module
from nexus.contracts import strict_json

@contextmanager
def running():
    with application(data) as (host,server):
        t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
        base='http://127.0.0.1:'+str(server.server_port)
        def call(path,value=None):
            r=Request(base+path,data=None if value is None else json.dumps(value,ensure_ascii=False).encode('utf-8'),headers={'Content-Type':'application/json','X-Nexus-Session':host.session})
            with urlopen(r,timeout=15) as f:return json.load(f)
        try:yield host,call
        finally:server.shutdown();t.join(10)

checks=[]
try:
    original='Corrige este texto: Isto é um ezemplo.'
    # Bytes after the colon, including the original space, are preserved.
    body=original.split(':',1)[1].encode('utf-8')
    payload={'text':original,'filename':'','attachment':''}
    with running() as (host,call):
        preview=call('/api/interpret',{'text':original})
        assert preview['source_kind']=='inline_text' and preview['status']=='RESOLVED'
        assert call('/api/runs')==[]
        prepared=call('/api/prepare-run',payload)
        assert prepared['process']=='proofread' and prepared['attachment_sha256']==hashlib.sha256(body).hexdigest()
        assert call('/api/runs')==[]
        checks.append('pedido_sem_anexo_e_proposta_sem_execucao')
        run=call('/api/confirm-run',{'ticket':prepared['ticket'],'confirmed':True,**payload})['run_id']
        deadline=time.monotonic()+160
        while time.monotonic()<deadline:
            state=call('/api/runs/'+run)
            if state['status']!='RUNNING':break
            time.sleep(.3)
        assert state['status']=='HUMAN_REQUIRED',state.get('message',state['status'])
        assert state['result']['ai_calls']==0
        evidence=json.loads(state['result']['evidence'][0]['value'])
        assert evidence['matches']>=1 and 'ezemplo' in state['content']
        assert (data/'runs'/run/'input.bin').read_bytes()==body
        saved=strict_json((data/'runs'/run/'request.json').read_bytes())
        assert saved['text']==original
        assert not any((data/'canonical').iterdir())
        checks.append('languagetool_real_windows_sem_ia_com_alerta')
        checks.append('fonte_pedido_resultado_ligados_e_original_preservado')
        content=state['content']
    original_launch=host_module.launch_confined
    def ARCHIVE_REDACTED_04(*a,**kw):raise AssertionError('Reinicio nao pode repetir ferramenta')
    host_module.launch_confined=ARCHIVE_REDACTED_04
    try:
        with running() as (host,call):
            state=call('/api/runs/'+run)
            assert state['status']=='HUMAN_REQUIRED' and state['content']==content
            assert len(call('/api/runs'))==1 and host.tickets=={}
            assert not any((data/'canonical').iterdir())
    finally:host_module.launch_confined=original_launch
    checks.append('reinicio_sem_reexecutar_ou_aprovar')
    result={'status':'PASS','checks':checks,'matches':evidence['matches'],'version':evidence['version'],'result':content,'coverage':'Um pedido de revisao natural, LanguageTool real confinado no Windows, proveniencia e reinicio. Nao prova todos os erros de portugues nem outras ferramentas.'}
except Exception as e:
    result={'status':'FAIL','error_type':type(e).__name__,'message':str(e)[:700],'checks':checks}
args.report.parent.mkdir(parents=True,exist_ok=True)
args.report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
raise SystemExit(0 if result['status']=='PASS' else 1)
