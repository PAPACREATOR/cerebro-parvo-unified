"""Only test Nexus startup, loaded local model health and duplicate prevention."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, json, socket, subprocess, time, urllib.request, urllib.parse

ROOT=Path(r'C:\Nexus')
SERVICES=((18081,'nexus-qwen3-1.7b'),(18082,'nexus-qwen3-embedding-0.6b'))

def get(url,headers=None):
    request=urllib.request.Request(url,headers=headers or {})
    with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(request,timeout=4) as response:
        assert response.status==200
        return json.load(response)

def open_port(port):
    with socket.socket() as probe:
        probe.settimeout(.5)
        return probe.connect_ex(('127.0.0.1',port))==0

def launch():
    # This is the ordinary Nexus entry point, not either model executable.
    return subprocess.Popen([str(ROOT/'ambientes/host/Scripts/pythonw.exe'),'-X','utf8',str(ROOT/'abrir-nexus.py'),'--no-browser'],cwd=ROOT,creationflags=subprocess.CREATE_NO_WINDOW)

def models_ready():
    for port,alias in SERVICES:
        health=get(f'http://127.0.0.1:{port}/health')
        models=get(f'http://127.0.0.1:{port}/v1/models')
        assert health['status']=='ok'
        assert any(x.get('id')==alias for x in models['data'])
    status=json.loads((ROOT/'registos/ia-local-servicos.json').read_text('utf-8'))
    assert status['status']=='READY' and len(status['services'])==2
    return status

def test(cold=False):
    before={str(port):open_port(port) for port,_ in SERVICES}
    if cold:assert not any(before.values()),'O teste frio exige ambos os servidores inicialmente desligados.'
    began=datetime.now(timezone.utc)
    started=launch()
    deadline=time.monotonic()+210
    while time.monotonic()<deadline:
        try:status=models_ready();break
        except (OSError,ValueError,KeyError,AssertionError):
            try:
                current=json.loads((ROOT/'registos/ia-local-servicos.json').read_text('utf-8'))
                if (current['status']=='FAIL' and datetime.fromisoformat(current['updated_at'])>=began):
                    raise RuntimeError(current.get('error','Falha do supervisor local.'))
            except (OSError,ValueError,KeyError):pass
            time.sleep(.5)
    else:raise AssertionError('Os dois modelos nao ficaram prontos no tempo permitido; consultar ia-local-servicos.json.')
    url=urllib.parse.urlsplit((ROOT/'dados/launch-url.txt').read_text('utf-8').strip())
    token=urllib.parse.parse_qs(url.fragment)['session'][0]
    runs=get(f'http://127.0.0.1:{url.port}/api/runs',{'X-Nexus-Session':token})
    assert all(x['status']!='RUNNING' for x in runs)
    previous=status
    duplicate=launch();assert duplicate.wait(timeout=20)==0
    status=models_ready()
    assert status['supervisor_pid']==previous['supervisor_pid']
    assert status['services']==previous['services']
    command="Get-NetTCPConnection -State Listen -ErrorAction Stop | Where-Object LocalPort -in 18081,18082 | Select-Object LocalAddress,LocalPort,OwningProcess | ConvertTo-Json -Compress"
    checked=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',command],capture_output=True,timeout=20,check=True)
    bindings=json.loads(checked.stdout.decode('utf-8-sig'));bindings=bindings if isinstance(bindings,list) else [bindings]
    assert {x['LocalPort'] for x in bindings}=={18081,18082}
    assert all(x['LocalAddress']=='127.0.0.1' for x in bindings)
    return {'status':'PASS','tested_at':time.strftime('%Y-%m-%d %H:%M:%S'),
            'entry_point':str(ROOT/'Abrir Nexus.cmd'),'cold_start':cold,'ports_open_before':before,
            'checks':['entrada_normal_inicia_os_dois_modelos','modelos_carregados_health_ok_e_alias_confirmado',
                      'segunda_abertura_sem_duplicar_servidores','apenas_127.0.0.1','sem_tarefas_de_produto_iniciadas'],
            'services':status['services'],'bindings':bindings,'history_count':len(runs),
            'inference':'NOT_RUN','search':'NOT_RUN','podcast':'NOT_RUN','music':'NOT_RUN'}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cold',action='store_true')
    parser.add_argument('--report',type=Path,default=ROOT/'registos/arranque-modelos-teste.json')
    args=parser.parse_args()
    try:result=test(args.cold)
    except Exception as error:result={'status':'FAIL','error_type':type(error).__name__,'message':str(error)[:500]}
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
    raise SystemExit(0 if result['status']=='PASS' else 1)
