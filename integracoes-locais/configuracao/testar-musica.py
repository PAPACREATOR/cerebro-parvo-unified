import os,json
from pathlib import Path
os.environ['ACESTEP_CHECKPOINTS_DIR']='C:/Nexus/ferramentas/nexus-tools/models/ace-step'
from acestep.handler import AceStepHandler
from acestep.llm_inference import LLMHandler
from acestep.inference import generate_music,GenerationParams,GenerationConfig
root=Path('C:/Nexus/ferramentas/nexus-tools/ACE-Step-1.5')
handler=AceStepHandler()
message,ok=handler.initialize_service(str(root),'acestep-v15-turbo',device='cuda',use_flash_attention=False,compile_model=False,offload_to_cpu=True,offload_dit_to_cpu=True)
print(message,flush=True)
assert ok
result=generate_music(handler,LLMHandler(),GenerationParams(caption='Gentle instrumental piano, calm documentary background, no vocals',lyrics='[Instrumental]',instrumental=True,duration=10,inference_steps=8,thinking=False,use_cot_metas=False,use_cot_caption=False,use_cot_language=False,seed=42),GenerationConfig(batch_size=1,audio_format='wav'),save_dir='C:/Nexus/registos/musica-teste-real')
print(result,flush=True)
assert result.success
Path('C:/Nexus/registos/musica-teste-real.json').write_text(json.dumps({'status':'PASS','result':str(result)},ensure_ascii=False,indent=2),encoding='utf-8')
