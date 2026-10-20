"""Real Windows native experiment. Missing execution/ERROR is never a PASS."""
import json
import os
from pathlib import Path
import socket
import sys

import pytest

from nexus.host import process_environment
from nexus.windows_sandbox import _API, MODIFY, launch_confined

SCRIPT = r'''
import ctypes as C, errno, json, os, socket, subprocess, sys, winreg
from pathlib import Path
plan=json.loads(Path('input.json').read_text())
observations={}
def access_denied(e):
    winerror=getattr(e,'winerror',None)
    return winerror==5 or (winerror is None and e.errno in (errno.EACCES,errno.EPERM))
denied=0
errors=[]
for i in range(10000):
    area=plan['areas'][i % len(plan['areas'])]
    action=('overwrite','create','delete','rename','mkdir')[(i//len(plan['areas'])) % 5]
    path=Path(area)/('original' if action in ('overwrite','delete','rename') else 'new-'+str(i))
    try:
        if action=='overwrite': path.write_bytes(b'changed')
        elif action=='create': path.write_bytes(b'new')
        elif action=='delete': path.unlink()
        elif action=='rename': path.rename(path.with_name('renamed-'+str(i)))
        elif action=='mkdir': path.mkdir()
        errors.append([i,action,'ALLOWED'])
    except OSError as e:
        if access_denied(e): denied+=1
        else: errors.append([i,action,type(e).__name__,e.errno,getattr(e,'winerror',None)])
try:
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,plan['registry_key'],0,winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key,'original',0,winreg.REG_SZ,'changed')
    observations['registry:write']='ALLOWED'
except OSError as e:
    observations['registry:write']='DENIED' if access_denied(e) else 'ERROR'
for name in ('creative','canonical'):
    try:
        (Path(plan['by_name'][name])/'original').read_bytes()
        observations[name+':read']='ALLOWED'
    except OSError as e:
        observations[name+':read']='DENIED' if access_denied(e) else 'ERROR'
s=None
try:
    s=socket.socket()
    s.settimeout(2)
    s.connect(('127.0.0.1',plan['port']))
    observations['network']='ALLOWED'
except OSError as e:
    fw=C.WinDLL('Firewallapi',use_last_error=True)
    diagnostic=fw.NetworkIsolationDiagnoseConnectFailureAndGetInfo
    diagnostic.argtypes=[C.c_wchar_p,C.POINTER(C.c_int)]
    diagnostic.restype=C.c_ulong
    missing=C.c_int()
    rc=diagnostic('127.0.0.1',C.byref(missing))
    observations['network_diagnostic']={'result':rc,'missing_capability':missing.value,'exception':type(e).__name__,'winerror':getattr(e,'winerror',None)}
    # A timeout alone is not a security PASS. Native diagnosis must identify a
    # missing network capability; live Host connections bracket this attempt.
    native_denial=getattr(e,'winerror',None)==10013 or e.errno==10013
    observations['network']='DENIED' if native_denial or (rc==0 and missing.value in (1,2,3)) else 'ERROR:'+str(e)
finally:
    if s is not None: s.close()
Path('allowed.txt').write_text('work-result')
observations['work']=Path('allowed.txt').read_text()
child_code="from pathlib import Path; p=Path(%r);\ntry: p.write_bytes(b'child-change'); print('ALLOWED')\nexcept OSError as e: print('DENIED' if (getattr(e,'winerror',None)==5 or (getattr(e,'winerror',None) is None and e.errno in (1,13))) else 'ERROR')" % str(Path(plan['areas'][0])/'original')
child=subprocess.run([sys.executable,'-I','-c',child_code],capture_output=True,timeout=10,creationflags=subprocess.CREATE_NO_WINDOW)
observations['child']=child.stdout.decode().strip() if child.returncode==0 else 'ERROR'
print(json.dumps({'denied':denied,'errors':errors[:30],'observations':observations}))
'''


def test_real_native_boundary_10000_file_attacks_and_descendant(tmp_path):
    assert os.name == 'nt', 'Native Windows test NOT RUN on this OS'
    work = tmp_path / 'assigned-work'
    work.mkdir()
    areas = {}
    for name in ('kernel','creative','canonical','outside-install','all-app-packages'):
        folder = tmp_path / name
        folder.mkdir()
        (folder/'original').write_bytes(b'synthetic-original')
        areas[name] = str(folder)
    # Deliberately permissive synthetic AAP directory: regular AppContainer
    # inherits this shared grant. LPAC must deny it without weakening its ACL.
    api=_API()
    aap=api.P()
    import ctypes as C
    convert=api.a.ConvertStringSidToSidW
    convert.restype=C.c_int
    convert.argtypes=[C.c_wchar_p,C.POINTER(api.P)]
    assert convert('S-1-15-2-1',C.byref(aap))
    try:
        api.acl(areas['all-app-packages'],aap,MODIFY)
        api.low_label(areas['all-app-packages'])
    finally:
        api.k.LocalFree(aap)
    import uuid, winreg
    registry_key = 'Software/NexusConfinement/' + uuid.uuid4().hex
    registry_key = registry_key.replace('/', chr(92))
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER,registry_key) as key:
        winreg.SetValueEx(key,'original',0,winreg.REG_SZ,'synthetic-original')
    with socket.socket() as listener:
        listener.bind(('127.0.0.1',0)); listener.listen()
        port = listener.getsockname()[1]
        with socket.create_connection(('127.0.0.1',port),timeout=2):
            connection,_=listener.accept();connection.close()
        (work/'input.json').write_text(json.dumps({'areas':list(areas.values()),'by_name':areas,'port':port,'registry_key':registry_key}))
        with launch_confined([sys.executable,'-I','-c',SCRIPT],cwd=work,
                             env=process_environment(work),read_roots=(sys.prefix,sys.base_prefix)) as proc:
            stdout, stderr = proc.communicate(timeout=120)
            code = proc.returncode
        assert code == 0, stderr.decode(errors='replace')
        with socket.create_connection(('127.0.0.1',port),timeout=2):
            connection,_=listener.accept();connection.close()
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,registry_key) as key:
        assert winreg.QueryValueEx(key,'original')[0] == 'synthetic-original'
    winreg.DeleteKey(winreg.HKEY_CURRENT_USER,registry_key)
    result = json.loads(stdout)
    evidence = os.environ.get('NEXUS_NATIVE_EVIDENCE')
    if evidence:
        target=Path(evidence);target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
    result['observations'].pop('network_diagnostic',None)
    assert result['denied'] == 10000, result
    assert not result['errors'], result
    assert result['observations'] == {'creative:read':'DENIED','canonical:read':'DENIED',
                                     'network':'DENIED','registry:write':'DENIED','work':'work-result','child':'DENIED'}, result
    assert all((Path(folder)/'original').read_bytes()==b'synthetic-original' for folder in areas.values())
    assert all(sorted(p.name for p in Path(folder).iterdir())==['original'] for folder in areas.values())


def test_native_bad_command_never_launches(tmp_path):
    from nexus.contracts import Blocked
    with pytest.raises(Blocked):
        launch_confined(['not-an-absolute-program','\x00'],cwd=tmp_path,env={})


def test_directory_enumeration_does_not_authorize_unassigned_file(tmp_path):
    assert os.name == "nt", "Native Windows test NOT RUN on this OS"
    work = tmp_path / "assigned"
    work.mkdir()
    directory = tmp_path / "dependency"
    directory.mkdir()
    selected = directory / "selected"
    selected.write_bytes(b"selected-data")
    protected = directory / "original"
    protected.write_bytes(b"original")
    import ctypes as C
    api = _API()
    def acl_bytes(path):
        acl, descriptor = api.P(), api.P()
        assert api.a.GetNamedSecurityInfoW(str(path), 1, 4, None, None,
                                         C.byref(acl), None, C.byref(descriptor)) == 0
        try:
            assert acl
            size = int.from_bytes(C.string_at(acl, 4)[2:4], "little")
            return C.string_at(acl, size)
        finally:
            api.k.LocalFree(descriptor)
    original_acl = acl_bytes(protected)
    code = (
        "import json;from pathlib import Path;"
        f"folder=Path({str(directory)!r});"
        f"selected=Path({str(selected)!r});protected=Path({str(protected)!r});"
        "assert 'original' in {p.name for p in folder.iterdir()};"
        "assert selected.read_bytes()==b'selected-data';\n"
        "try: protected.read_bytes();print('ALLOWED')\n"
        "except PermissionError: print('DENIED')"
    )
    with launch_confined([sys.executable, "-I", "-c", code], cwd=work,
                         env=process_environment(work),
                         read_roots=(sys.prefix, sys.base_prefix, selected),
                         read_dirs=(directory,)) as process:
        stdout, stderr = process.communicate(timeout=10)
        assert process.returncode == 0, stderr.decode(errors="replace")
    assert stdout.strip() == b"DENIED"
    assert protected.read_bytes() == b"original"
    assert selected.read_bytes() == b"selected-data"
    assert acl_bytes(protected) == original_acl
