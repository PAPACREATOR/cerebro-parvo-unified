"""Standalone local WSL avatar launcher; original Windows API remains intact."""
import subprocess,sys,datetime
from pathlib import Path
R=Path('C:/Nexus')
def linux(p):
    p=Path(p).resolve()
    if p.drive.upper()!='C:': raise ValueError('Coloca os ficheiros em C:\\Nexus antes de continuar.')
    return '/mnt/c/'+p.as_posix()[3:]
def main():
    portrait=Path(sys.argv[1] if len(sys.argv)>1 else input('Caminho da imagem do avatar: ').strip('" ')).resolve()
    audio=Path(sys.argv[2] if len(sys.argv)>2 else input('Caminho do audio: ').strip('" ')).resolve()
    if not portrait.is_file() or not audio.is_file(): raise ValueError('Imagem ou audio nao encontrado.')
    folder=R/'dados/avatar-videos'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    folder.mkdir(parents=True,exist_ok=False)
    wav=folder/'audio.wav'; output=folder/'avatar.mp4'
    subprocess.run([str(R/'ferramentas/ffmpeg/ffmpeg.exe'),'-nostdin','-v','error','-i',str(audio),'-ac','1','-ar','16000',str(wav)],check=True)
    subprocess.run(['wsl.exe','-d','Nexus','-u','root','--exec','/opt/nexus-avatar/bin/python','-m','notebook_avatar.worker','--audio',linux(wav),'--avatar',linux(portrait),'--output',linux(output),'--checkpoint',linux(R/'ferramentas/nexus-tools/OpenNotebook/data/avatar-models/wav2lip.pth'),'--detector',linux(R/'ferramentas/nexus-tools/OpenNotebook/data/avatar-models/s3fd.pth'),'--ffmpeg','/usr/bin/ffmpeg','--device','cpu','--batch-size','2'],check=True)
    print('Video criado: '+str(output))
if __name__=='__main__': main()
