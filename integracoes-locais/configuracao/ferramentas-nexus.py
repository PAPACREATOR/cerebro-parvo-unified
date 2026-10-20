import os,subprocess,sys,time,webbrowser,urllib.request
from pathlib import Path
R=Path('C:/Nexus'); T=R/'ferramentas/nexus-tools'
def ready(url):
    try:
        with urllib.request.urlopen(url,timeout=2) as response:return response.status==200
    except Exception:return False
def start(tool):
    env=dict(os.environ,PYTHONUTF8='1',HF_HOME=str(R/'modelos/huggingface'))
    env['PATH']=str(R/'ferramentas/ffmpeg')+';'+env.get('PATH','')
    if tool=='imagens':
        cwd=T/'Forge'; args=[cwd/'venv/Scripts/python.exe','-u','-X','utf8','launch.py','--api','--port','7861','--skip-version-check','--skip-install','--deforum-api']; url='http://127.0.0.1:7861'
    elif tool=='musica':
        cwd=T/'ACE-Step-1.5'; env['ACESTEP_CHECKPOINTS_DIR']=str(T/'models/ace-step')
        args=[cwd/'.venv/Scripts/python.exe','-u','-X','utf8','-m','acestep.acestep_v15_pipeline','--server-name','127.0.0.1','--port','8001','--init_service','true','--init_llm','false','--config_path','acestep-v15-turbo','--device','cuda','--offload_to_cpu','true','--offload_dit_to_cpu','true','--use_flash_attention','false','--quantization','none','--enable-api']; url='http://127.0.0.1:8001'
    elif tool=='transcricao':
        cwd=T/'Speaches'; env.update(ENABLE_UI='true',WHISPER__INFERENCE_DEVICE='cpu',WHISPER__COMPUTE_TYPE='int8')
        args=[cwd/'.venv/Scripts/python.exe','-u','-X','utf8','-m','uvicorn','speaches.main:create_app','--factory','--host','127.0.0.1','--port','8002']; url='http://127.0.0.1:8002'
    elif tool=='video':
        cwd=T/'MoneyPrinterTurbo'; args=[cwd/'.venv/Scripts/python.exe','-m','streamlit','run','webui/Main.py','--server.address','127.0.0.1','--server.port','8501','--server.headless','true']; url='http://127.0.0.1:8501'
    elif tool=='cadernos':
        cwd=R; args=[R/'ambientes/host/Scripts/python.exe','-X','utf8',R/'configuracao/servicos-open-notebook.py']; url='http://127.0.0.1:3000'
    else:raise ValueError(tool)
    if not ready(url):
        with (R/'registos'/('ferramenta-'+tool+'.log')).open('ab') as log:
            process=subprocess.Popen([str(x) for x in args],cwd=cwd,env=env,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
        for _ in range(180):
            if ready(url):break
            if process.poll() is not None:raise RuntimeError('Consultar o registo de '+tool)
            time.sleep(1)
        else:raise TimeoutError('Ainda a iniciar; consultar registos.')
    webbrowser.open(url)
if __name__=='__main__':
    # Internal explicit service call only; no interactive tool-selection menu.
    if len(sys.argv)==2:
        start(sys.argv[1])
