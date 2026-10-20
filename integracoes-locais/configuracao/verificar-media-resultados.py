import json,subprocess,wave,math,array
from pathlib import Path
R=Path('C:/Nexus'); F=R/'ferramentas/nexus-tools'; results=[]
def probe(path,required,duration):
    data=json.loads(subprocess.check_output([str(R/'ferramentas/ffmpeg/ffprobe.exe'),'-v','error','-show_streams','-show_format','-of','json',str(path)]))
    assert required <= {x['codec_type'] for x in data['streams']}
    assert float(data['format']['duration'])>=duration
    subprocess.run([str(R/'ferramentas/ffmpeg/ffmpeg.exe'),'-v','error','-i',str(path),'-f','null','-'],check=True,capture_output=True)
    return data
def check(name,fn):
    try:detail=fn(); results.append(dict(test=name,status='PASS',detail=detail))
    except Exception as e:results.append(dict(test=name,status='FAIL',detail=str(e)))
def music():
    path=next((R/'registos/musica-teste-real').glob('*.wav'))
    probe(path,{'audio'},9)
    raw=subprocess.check_output([str(R/'ferramentas/ffmpeg/ffmpeg.exe'),'-v','error','-i',str(path),'-f','s16le','-acodec','pcm_s16le','-'])
    samples=array.array('h',raw)
    assert math.sqrt(sum(x*x for x in samples)/len(samples))>10
    return 'Musica ACE-Step gerada localmente; audio descodificado e nao silencioso: '+str(path)
def video():
    path=F/'MoneyPrinterTurbo/storage/tasks/bbf9ccbd-e329-474f-bdba-632504c81010/final-1.mp4'
    probe(path,{'video','audio'},4.9);return 'Montagem MoneyPrinterTurbo com imagem e audio: '+str(path)
def avatar():
    path=R/'registos/avatar-teste-real.mp4';probe(path,{'video','audio'},0.8)
    return 'Worker WSL CPU; sincronizacao labial com imagem de teste: '+str(path)
def animation():
    report=json.loads((R/'registos/deforum-teste-real.json').read_text())
    assert report['status']=='SUCCEEDED'
    path=Path(report['outdir'])/(report['timestring']+'.mp4');data=probe(path,{'video'},0.4)
    assert int(data['streams'][0]['nb_frames'])>=2
    return 'Animacao Deforum real: '+str(path)
def transcription():
    report=json.loads((R/'registos/ferramentas-api-teste-real.json').read_text(encoding='utf-8'))
    assert report['speaches']['status']=='PASS' and report['speaches']['transcript'].strip()
    return 'Transcricao real local com Whisper small; texto requer revisao humana'
check('musica-resultado-real',music);check('montagem-video-resultado-real',video);check('avatar-resultado-real',avatar);check('animacao-resultado-real',animation);check('transcricao-resultado-real',transcription)
(R/'registos/media-resultados-verificados.json').write_text(json.dumps(dict(results=results,scope='Revalidacao dos ficheiros produzidos nos testes reais; nao avalia todos os modos das ferramentas'),ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(results,ensure_ascii=False))
raise SystemExit(1 if any(x['status']!='PASS' for x in results) else 0)
