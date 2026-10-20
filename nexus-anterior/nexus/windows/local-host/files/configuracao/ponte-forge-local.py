"""Local OpenAI image protocol -> installed Forge API. No cloud calls or Store access."""
import base64,hashlib,hmac,json,msvcrt,os,socket,struct,subprocess,threading,time,uuid
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import URLError

ROOT=Path('C:/Nexus'); HOST='127.0.0.1'; PORT=8970
MODEL='nexus-forge-sd15'; KEY='nexus-local-image-routing'
BACKEND='http://127.0.0.1:7861'; SLOT=threading.BoundedSemaphore(1)
MAX_BODY=32768; MAX_IMAGE=25*1024*1024

class Rejected(Exception):
    def __init__(self,status,message):self.status=status;self.message=message

def unique(pairs):
    d={}
    for k,v in pairs:
        if k in d:raise ValueError('Repeated key')
        d[k]=v
    return d

def validate(d):
    if not isinstance(d,dict) or set(d)-{'model','prompt','n','size','response_format'}:raise Rejected(400,'Unsupported image request')
    if d.get('model')!=MODEL or type(d.get('n',1)) is not int or d.get('n',1)!=1:raise Rejected(400,'Select the installed model and one image')
    text=d.get('prompt')
    if not isinstance(text,str) or not text.strip() or len(text)>4000:raise Rejected(400,'Prompt must contain 1 to 4000 characters')
    try:text.encode('utf-8')
    except UnicodeError:raise Rejected(400,'Prompt must be valid UTF-8') from None
    if d.get('response_format','b64_json')!='b64_json':raise Rejected(400,'Only b64_json is supported')
    size=d.get('size','512x512')
    if size not in ('512x512','768x512','512x768'):raise Rejected(400,'Supported sizes: 512x512, 768x512, 512x768')
    return text,tuple(map(int,size.split('x')))

def backend(path,payload=None,timeout=10):
    req=Request(BACKEND+path,data=None if payload is None else json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
    with urlopen(req,timeout=timeout) as response:
        raw=response.read(40*1024*1024+1)
        if len(raw)>40*1024*1024:raise Rejected(502,'Backend response exceeds image limit')
        return json.loads(raw)

def ensure_backend():
    try:
        catalog=backend('/sdapi/v1/sd-models')
        if not isinstance(catalog,list) or not any('v1-5-pruned-emaonly' in str(x.get('title','')) for x in catalog):raise Rejected(503,'Installed Forge checkpoint unavailable')
        return
    except Rejected:raise
    except (URLError,OSError):pass
    with socket.socket() as probe:
        if probe.connect_ex((HOST,7861))==0:raise Rejected(503,'Forge port occupied by an unverified service')
    cwd=ROOT/'ferramentas/nexus-tools/Forge'
    env=dict(os.environ,PYTHONUTF8='1',HF_HOME=str(ROOT/'modelos/huggingface'))
    env['PATH']=str(ROOT/'ferramentas/ffmpeg')+os.pathsep+env.get('PATH','')
    with (ROOT/'registos/forge-image-provider.log').open('ab') as log:
        process=subprocess.Popen([str(cwd/'venv/Scripts/python.exe'),'-u','-X','utf8','launch.py','--api','--port','7861','--skip-version-check','--skip-install','--deforum-api'],cwd=cwd,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
    until=time.monotonic()+130
    while time.monotonic()<until:
        if process.poll() is not None:raise Rejected(503,'Forge startup failed; inspect local service log')
        try:
            if isinstance(backend('/sdapi/v1/sd-models',timeout=2),list):return
        except (URLError,OSError):pass
        time.sleep(1)
    raise Rejected(504,'Forge is still starting; request not generated')

def generate(text,size):
    ensure_backend()
    result=backend('/sdapi/v1/txt2img',{'prompt':text,'negative_prompt':'text, watermark','width':size[0],'height':size[1],'steps':20,'batch_size':1,'n_iter':1,'seed':-1,'override_settings':{'sd_model_checkpoint':'v1-5-pruned-emaonly.safetensors'},'override_settings_restore_afterwards':True},timeout=180)
    try:
        encoded=result['images'][0];raw=base64.b64decode(encoded,validate=True)
        if len(raw)>MAX_IMAGE or raw[:8]!=b'\x89PNG\r\n\x1a\n' or struct.unpack('>II',raw[16:24])!=size:raise ValueError()
    except (KeyError,ValueError,IndexError,TypeError,struct.error):raise Rejected(502,'Forge returned an invalid image') from None
    trace={'id':uuid.uuid4().hex,'timestamp':time.time(),'provider':'Forge','model':MODEL,'input_sha256':hashlib.sha256(text.encode()).hexdigest(),'image_sha256':hashlib.sha256(raw).hexdigest(),'size':size}
    with (ROOT/'registos/forge-provider-traces.jsonl').open('a',encoding='utf-8') as log:log.write(json.dumps(trace)+'\n')
    return {'created':int(time.time()),'data':[{'b64_json':encoded}],'nexus_trace_id':trace['id']}

class Server(ThreadingHTTPServer):
    daemon_threads=True;allow_reuse_address=False
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def setup(self):super().setup();self.connection.settimeout(15)
    def reply(self,status,value):
        body=json.dumps(value).encode();self.send_response(status)
        self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store');self.send_header('Connection','close');self.end_headers();self.close_connection=True;self.wfile.write(body)
    def guard(self,auth=True):
        if self.client_address[0]!=HOST or self.headers.get_all('Host') not in ([f'{HOST}:{PORT}'],[f'localhost:{PORT}']):raise Rejected(403,'Local requests only')
        if self.headers.get('Origin') and self.headers.get('Origin') not in (f'http://{HOST}:{PORT}',f'http://localhost:{PORT}'):raise Rejected(403,'Origin not permitted')
        if auth:
            values=self.headers.get_all('Authorization') or []
            if len(values)!=1 or not hmac.compare_digest(values[0].encode(),('Bearer '+KEY).encode()):raise Rejected(401,'Local routing key required')
    def fail(self,e):self.reply(e.status,{'error':{'message':e.message,'type':'local_image_error'}})
    def do_GET(self):
        try:
            self.guard(self.path!='/health')
            if self.path=='/health':self.reply(200,{'status':'ready','service':'nexus-forge-image-bridge','backend_generation_checked':False})
            elif self.path=='/v1/models':self.reply(200,{'data':[{'id':MODEL,'object':'model','owned_by':'nexus-local'}]})
            else:raise Rejected(404,'Endpoint unavailable')
        except Rejected as e:self.fail(e)
    def do_POST(self):
        acquired=False
        try:
            self.guard()
            if self.path!='/v1/images/generations':raise Rejected(404,'Endpoint unavailable')
            lengths=self.headers.get_all('Content-Length') or []
            if self.headers.get('Transfer-Encoding') or len(lengths)!=1 or not lengths[0].isdigit():raise Rejected(400,'Invalid body length')
            length=int(lengths[0])
            if not 0<length<=MAX_BODY:raise Rejected(413,'Image request too large')
            if self.headers.get_content_type()!='application/json':raise Rejected(415,'JSON required')
            try:d=json.loads(self.rfile.read(length).decode('utf-8'),object_pairs_hook=unique)
            except (ValueError,UnicodeError,RecursionError):raise Rejected(400,'Invalid JSON') from None
            text,size=validate(d)
            acquired=SLOT.acquire(blocking=False)
            if not acquired:raise Rejected(409,'One image is already being generated; no new generation submitted')
            self.reply(200,generate(text,size))
        except Rejected as e:self.fail(e)
        except (BrokenPipeError,ConnectionResetError):self.close_connection=True
        except (URLError,OSError,ValueError):self.fail(Rejected(502,'Local image backend failed; no automatic resubmission'))
        finally:
            if acquired:SLOT.release()

def main():
    with (ROOT/'registos/forge-provider.lock').open('a+b') as lock:
        lock.seek(0)
        try:msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        except OSError:return
        with Server((HOST,PORT),Handler) as server:server.serve_forever()
if __name__=='__main__':main()
