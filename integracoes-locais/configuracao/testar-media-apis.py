import json,base64,urllib.request,uuid
from pathlib import Path
R=Path('C:/Nexus'); out=R/'registos'; report={}
def call(url,data=None,headers=None):
    req=urllib.request.Request(url,data=data,headers=headers or {})
    with urllib.request.urlopen(req,timeout=240) as response:return json.load(response)
if __name__=='__main__':
    image=call('http://127.0.0.1:7861/sdapi/v1/txt2img',json.dumps({'prompt':'a blue ceramic cup on a wooden table, simple photograph','negative_prompt':'text, watermark','steps':4,'width':256,'height':256,'seed':42,'batch_size':1}).encode(),{'Content-Type':'application/json'})
    target=out/'forge-imagem-teste.png'; target.write_bytes(base64.b64decode(image['images'][0]))
    assert target.read_bytes().startswith(b'\x89PNG')
    report['forge']={'status':'PASS','file':str(target)}
    (out/'ferramentas-api-teste-real.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('FORGE_RENDER_PASS',flush=True)
    boundary=uuid.uuid4().hex; chunks=[]
    for key,value in [('model','Systran/faster-whisper-small'),('language','pt')]:
        chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode())
    chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="teste.mp3"\r\nContent-Type: audio/mpeg\r\n\r\n'.encode()+(out/'moneyprinter-audio-teste.mp3').read_bytes()+b'\r\n')
    chunks.append(f'--{boundary}--\r\n'.encode())
    result=call('http://127.0.0.1:8002/v1/audio/transcriptions',b''.join(chunks),{'Content-Type':'multipart/form-data; boundary='+boundary})
    assert result.get('text','').strip()
    report['speaches']={'status':'PASS','transcript':result['text']}
    (out/'ferramentas-api-teste-real.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('SPEACHES_TRANSCRIPTION_PASS',flush=True)

