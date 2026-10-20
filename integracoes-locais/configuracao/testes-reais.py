import json, subprocess, sys, datetime, os
import time
from urllib.request import urlopen
from pathlib import Path
ROOT=Path(r'C:\Nexus')
OUT=ROOT/'registos'/'testes-reais'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
OUT.mkdir(parents=True,exist_ok=True)
results=[]
subprocess.Popen([str(ROOT/'ambientes/host/Scripts/pythonw.exe'),'-X','utf8',str(ROOT/'configuracao/servicos-open-notebook.py')],creationflags=subprocess.CREATE_NO_WINDOW)
until=time.monotonic()+150
while time.monotonic()<until:
    try:
        with urlopen('http://127.0.0.1:5055/health',timeout=2) as response:
            if response.status==200:break
    except Exception:pass
    time.sleep(1)
def command(name,args,timeout=120):
    p=subprocess.run([str(x) for x in args],capture_output=True,timeout=timeout)
    (OUT/(name+'.log')).write_bytes(p.stdout+b'\n'+p.stderr)
    if p.returncode: raise RuntimeError('Codigo '+str(p.returncode)+'; consultar '+name+'.log')
    return p.stdout
def test(name,fn):
    try: detail=fn(); status='PASS'
    except Exception as e: detail=str(e); status='FAIL'
    results.append(dict(test=name,status=status,detail=detail))
    print(name+': '+status,flush=True)
def video():
    target=OUT/'video-teste.mp4'
    command('video-render',[ROOT/'ferramentas/ffmpeg/ffmpeg.exe','-hide_banner','-y','-f','lavfi','-i','color=c=blue:s=320x240:r=25','-f','lavfi','-i','sine=frequency=440:sample_rate=44100','-t','1','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac',target])
    info=json.loads(command('video-inspecao',[ROOT/'ferramentas/ffmpeg/ffprobe.exe','-v','error','-show_streams','-show_format','-of','json',target]))
    assert {'video','audio'} <= {s['codec_type'] for s in info['streams']}
    assert float(info['format']['duration'])>=1
    return 'MP4 real com imagem e audio: '+str(target)
def core():
    command('nexus-fluxo',[sys.executable,ROOT/'configuracao/testar-nucleo.py','--memory-source',ROOT/'dados','--report',OUT/'folha-real.json'],180)
    return 'Folha natural, verificacao Windows, aprovacao sintetica, reinicio e copia da memoria'
def language():
    source=OUT/'portugues.txt';source.write_text('Eu vai para casa.',encoding='utf-8')
    jar=ROOT/'ferramentas/nexus-tools/LanguageTool/LanguageTool-6.6/languagetool-commandline.jar'
    raw=command('portugues',[ROOT/'ferramentas/java/bin/java.exe','-Xmx512m','-jar',jar,'-l','pt-PT','-c','utf-8','--json',source])
    data=json.loads(raw.decode('utf-8-sig'));assert data.get('matches'),'Nao identificou erro no exemplo'
    return str(len(data['matches']))+' problemas identificados no texto sintetico'
def notebook():
    command('open-notebook-base',[sys.executable,ROOT/'configuracao/verificar-surreal-wsl.py'],60)
    command('open-notebook-api',[sys.executable,ROOT/'configuracao/verificar-open-notebook.py'],60)
    return 'Base WSL e API reais, perfis preservados, autenticacao verificada'
def model():
    output=command('modelo-local',[ROOT/'ferramentas/llama/llama-cli.exe','-m',ROOT/'ferramentas/nexus-tools/models/llamacpp/Qwen3-1.7B-Q8_0.gguf','-p','Complete: 2 + 2 =','-n','12','-c','512','-ngl','99','--no-conversation','--no-display-prompt','--simple-io'],120)
    assert output.strip(),'Sem texto gerado'
    return 'Inferencia real local; saida guardada no registo'
def mcp_notebook():
    command('open-notebook-mcp',[ROOT/'ambientes/open-notebook-mcp/Scripts/python.exe','-X','utf8',ROOT/'configuracao/testar-open-notebook-mcp.py'],120)
    return 'MCP real: 33 ferramentas, leituras autenticadas e erros controlados'
def fresh_music():
    command('ace-step-geracao',[ROOT/'ferramentas/nexus-tools/ACE-Step-1.5/.venv/Scripts/python.exe','-u','-X','utf8',ROOT/'configuracao/testar-musica.py'],360)
    return 'Nova geracao ACE-Step de 10 segundos nesta execucao'

def fresh_apis():
    command('imagem-transcricao',[sys.executable,'-u','-X','utf8',ROOT/'configuracao/testar-media-apis.py'],360)
    return 'Nova imagem Forge e nova transcricao Whisper small pela API'

def fresh_animation():
    command('deforum-geracao',[sys.executable,'-u','-X','utf8',ROOT/'configuracao/testar-deforum.py'],300)
    return 'Nova animacao Deforum nesta execucao'

test('video-imagem-audio',video)
test('nexus-fluxo-real',core)
test('correcao-portugues',language)
test('open-notebook-base-api',notebook)
test('open-notebook-mcp',mcp_notebook)
test('modelo-local',model)
test('ace-step-musica-nova',fresh_music)
test('forge-transcricao-novas',fresh_apis)
test('deforum-animacao-nova',fresh_animation)
command('media-resultados',[sys.executable,ROOT/'configuracao/verificar-media-resultados.py'],120)
results.extend(json.loads((ROOT/'registos/media-resultados-verificados.json').read_text(encoding='utf-8'))['results'])
report=dict(results=results,scope='Testes reais do nucleo e revalidacao de resultados multimedia; nao testa todos os modos e parametros',directory=str(OUT))
(OUT/'resultado.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'registos/ultimo-teste-real.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('Relatorio: '+str(OUT/'resultado.json'))
sys.exit(1 if any(x['status']!='PASS' for x in results) else 0)
