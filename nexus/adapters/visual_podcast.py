import os
import subprocess
import tempfile
import time
from hashlib import sha256
from nexus.utils import save_bytes, sha256_bytes


def _powershell_synthesize(text: str, out_wav: str) -> bool:
    # Create a small PowerShell script to synthesize speech via System.Speech
    script = f"Add-Type -AssemblyName System.Speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.SetOutputToWaveFile('{out_wav}'); $s.Speak([Console]::In.ReadToEnd()); $s.Dispose()"
    try:
        proc = subprocess.run([
            'powershell', '-NoProfile', '-NoLogo', '-Command', script
        ], input=text.encode('utf-8'), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        return proc.returncode == 0
    except Exception:
        return False


def _ffmpeg_create_video_from_audio(audio_path: str, out_mp4: str, duration: float = None) -> bool:
    # Use ffmpeg to create a video from a solid color and the audio track.
    # Command: ffmpeg -y -loop 1 -f lavfi -i color=c=white:s=1280x720 -i audio.wav -shortest -c:v libx264 -c:a aac out.mp4
    cmd = [
        'ffmpeg', '-y', '-hide_banner', '-loglevel', 'error',
        '-loop', '1', '-f', 'lavfi', '-i', 'color=c=white:s=1280x720',
        '-i', audio_path,
        '-shortest', '-c:v', 'libx264', '-c:a', 'aac', '-pix_fmt', 'yuv420p', out_mp4
    ]
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
        return proc.returncode == 0
    except Exception:
        return False


def create_visual_podcast(text: str, run_dir: str, filename: str = 'visual_podcast.mp4') -> dict:
    """Create a simple visual podcast: TTS -> WAV -> MP4 (white frame + audio).

    Writes files into run_dir and returns envelope-like dict with artifact info.
    If PowerShell or ffmpeg missing, returns status 'UNKNOWN' with message.
    """
    os.makedirs(run_dir, exist_ok=True)
    wav_path = os.path.join(run_dir, 'speech.wav')
    mp4_path = os.path.join(run_dir, filename)

    # 1) Synthesize via PowerShell SAPI
    ok = _powershell_synthesize(text, wav_path)
    if not ok or not os.path.exists(wav_path):
        return {'status': 'UNKNOWN', 'message': 'PowerShell SAPI unavailable or synthesis failed. Ensure PowerShell is present and execution policy allows scripts.'}

    # 2) Create MP4 using ffmpeg
    ok2 = _ffmpeg_create_video_from_audio(wav_path, mp4_path)
    if not ok2 or not os.path.exists(mp4_path):
        return {'status': 'FAIL', 'message': 'FFmpeg conversion failed or ffmpeg not installed.'}

    # 3) Compute sha256 and size
    with open(mp4_path, 'rb') as f:
        data = f.read()
    digest = sha256_bytes(data)
    size = len(data)

    return {'status': 'OK', 'artifact': {'path': mp4_path, 'sha256': digest, 'size_bytes': size}, 'trace': {'tool': 'powershell+synth + ffmpeg', 'time': time.time()}}
