"""Single local Nexus entry point; reopen an existing authenticated instance."""
from pathlib import Path
import subprocess,sys,msvcrt,json,urllib.request,urllib.parse,webbrowser,contextlib,traceback

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'dados'

def reopen():
    try:
        url=(DATA/'launch-url.txt').read_text(encoding='utf-8').strip()
        parts=urllib.parse.urlsplit(url)
        if parts.scheme!='http' or parts.hostname!='127.0.0.1' or not parts.port:return False
        token=urllib.parse.parse_qs(parts.fragment)['session'][0]
        request=urllib.request.Request(f'http://127.0.0.1:{parts.port}/api/runs',headers={'X-Nexus-Session':token})
        with urllib.request.urlopen(request,timeout=3) as response:
            if response.status!=200:return False
        if '--no-browser' not in sys.argv:webbrowser.open(url)
        print('Nexus ja aberto.',flush=True)
        return True
    except (OSError,ValueError,KeyError):return False

def main():
    DATA.mkdir(exist_ok=True)
    # Independent local service lock also makes reopening Nexus safe.
    # The writing surface opens while the two installed models load.
    subprocess.Popen([str(ROOT/'ambientes/host/Scripts/pythonw.exe'),'-X','utf8',str(ROOT/'configuracao/servicos-ia-local.py')],creationflags=subprocess.CREATE_NO_WINDOW)
    subprocess.Popen([str(ROOT/'ambientes/host/Scripts/pythonw.exe'),'-X','utf8',str(ROOT/'configuracao/ponte-piper-local.py')],creationflags=subprocess.CREATE_NO_WINDOW)
    subprocess.Popen([str(ROOT/'ambientes/host/Scripts/pythonw.exe'),'-X','utf8',str(ROOT/'configuracao/ponte-forge-local.py')],creationflags=subprocess.CREATE_NO_WINDOW)
    with (DATA/'host.lock').open('a+b') as lock:
        lock.seek(0)
        try:msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        except OSError:
            if reopen():return 0
            print('O Nexus esta a iniciar. Aguarda alguns segundos.',file=sys.stderr)
            return 1
        subprocess.Popen([str(ROOT/'ambientes/host/Scripts/pythonw.exe'),'-X','utf8',str(ROOT/'configuracao/servicos-open-notebook.py')],creationflags=subprocess.CREATE_NO_WINDOW)
        sys.path.insert(0,str(ROOT/'aplicacao'))
        from nexus.app import main as application_main
        sys.argv=[sys.argv[0],'--data',str(DATA)]+(['--no-browser'] if '--no-browser' in sys.argv else [])
        return application_main()

if __name__=='__main__':
    log=ROOT/'registos/arranque.log'
    log.parent.mkdir(exist_ok=True)
    with log.open('a',encoding='utf-8') as stream,contextlib.redirect_stdout(stream),contextlib.redirect_stderr(stream):
        try:result=main()
        except Exception:
            traceback.print_exc();result=1
        raise SystemExit(result)

