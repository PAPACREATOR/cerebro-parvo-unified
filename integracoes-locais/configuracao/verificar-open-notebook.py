from pathlib import Path
import json,urllib.request,urllib.error
r=Path(r'C:\Nexus');c=json.loads((r/'configuracao/notebook.json').read_text(encoding='utf-8'))
base='http://127.0.0.1:5055'; results={}
for path in ['/health','/api/notebooks','/api/episode-profiles','/api/speaker-profiles','/api/models']:
    request=urllib.request.Request(base+path,headers={'Authorization':'Bearer '+c['password']})
    with urllib.request.urlopen(request,timeout=20) as response:
        value=json.load(response);results[path]={'status':response.status,'count':len(value) if isinstance(value,list) else None}
try:
    urllib.request.urlopen(base+'/api/notebooks',timeout=10)
    raise RuntimeError('Pedido sem autenticacao foi aceite')
except urllib.error.HTTPError as e:assert e.code==401
report={'status':'PASS','authentication_required':True,'routes':results,'scope':'Leitura real da copia preservada; nao valida geracao podcast/avatar'}
(r/'registos/open-notebook-teste-real.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
