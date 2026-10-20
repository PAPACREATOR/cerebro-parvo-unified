import json,urllib.request,time
from pathlib import Path
R=Path('C:/Nexus'); base='http://127.0.0.1:7861'
def api(path,data=None):
    request=urllib.request.Request(base+path,data=json.dumps(data).encode() if data is not None else None,headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(request,timeout=180) as response:return json.load(response)
settings=json.loads((R/'ferramentas/nexus-tools/Forge/extensions/sd-forge-deforum/scripts/default_settings.txt').read_text(encoding='utf-8'))
settings.update(W=256,H=256,steps=4,max_frames=3,fps=4,animation_mode='2D',animation_prompts={'0':'A blue ceramic cup on a wooden table, photograph'},prompts={'0':'A blue ceramic cup on a wooden table, photograph'},use_depth_warping=False,diffusion_cadence=1,seed=42,seed_behavior='fixed',zoom='0:(1.01)',angle='0:(0)',translation_x='0:(0)',translation_y='0:(0)',skip_video_creation=False,ffmpeg_location='C:/Nexus/ferramentas/ffmpeg/ffmpeg.exe',batch_name='Nexus_Teste_Real_20261010',save_depth_maps=False,hybrid_composite='None',hybrid_motion='None')
job=api('/deforum_api/batches',{'deforum_settings':[settings],'options_overrides':{}})
print(json.dumps(job),flush=True)
(R/'registos/deforum-pedido-real.json').write_text(json.dumps(job,indent=2))
for _ in range(90):
    result=api('/deforum_api/jobs/'+job['job_ids'][0])
    (R/'registos/deforum-teste-real.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    status=result.get('status')
    if status in ('SUCCEEDED','FAILED','CANCELLED'):
        print(json.dumps(result),flush=True)
        assert status=='SUCCEEDED'
        break
    time.sleep(2)
else: raise TimeoutError('Animacao ainda em execucao; consultar registo.')
