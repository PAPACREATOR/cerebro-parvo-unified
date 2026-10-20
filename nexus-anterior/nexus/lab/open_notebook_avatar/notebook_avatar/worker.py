"""Isolated lipsync 0.1.0 worker: no shell=True, no pickle cache, bounded batch.

Accept only private staged paths supplied by AvatarService, not LLM output.
"""
import argparse
import os
import subprocess


def main():
    if os.name == "nt":
        # Direct invocation cannot bypass the real OS boundary. Load only the
        # installed Nexus package; no broad parent-folder or PYTHONPATH grant.
        import importlib.util
        import sys
        from pathlib import Path
        root = Path(__file__).parents[3]
        if "nexus" not in sys.modules:
            spec = importlib.util.spec_from_file_location("nexus", root / "__init__.py",
                                                        submodule_search_locations=[str(root)])
            package = importlib.util.module_from_spec(spec)
            sys.modules["nexus"] = package
            spec.loader.exec_module(package)
        from nexus.windows_sandbox import require_native_boundary
        require_native_boundary()
    parser = argparse.ArgumentParser()
    for flag in ("audio", "avatar", "output", "checkpoint", "detector", "ffmpeg"):
        parser.add_argument("--" + flag, required=True)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    parser.add_argument("--batch-size", type=int, default=8)
    args = parser.parse_args()
    import torch
    from lipsync import LipSync
    from lipsync.models.wav2lip import Wav2Lip
    if args.device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA unavailable")
    if not 1 <= args.batch_size <= 32:
        raise ValueError("invalid batch")
    torch.set_num_threads(min(4, os.cpu_count() or 1))

    class LocalLipSync(LipSync):
        def detect_faces_in_frames(self, images):
            # LipSync needs only bounding boxes. Reuse the existing SFD
            # detector directly, avoiding an unnecessary FAN landmark model,
            # torch.compile startup and its additional model downloads.
            from face_alignment.detection.sfd import FaceDetector
            detector = FaceDetector(device=self.device, path_to_detector=args.detector, verbose=False)
            boxes = []
            for image in images:
                faces = detector.detect_from_image(image)
                if len(faces) != 1:
                    raise ValueError("Avatar must contain exactly one detectable face")
                boxes.append(tuple(max(0, int(x)) for x in faces[0][:4]))
            return boxes

        def _load_model_for_inference(self):
            # Official Wav2Lip checkpoints wrap state_dict; lipsync 0.1.0
            # assumes a bare dict. Support both without unsafe pickle loading.
            state = torch.load(self.checkpoint_path, map_location=self.device, weights_only=True)
            state = state.get("state_dict", state)
            model = Wav2Lip()
            model.load_state_dict({k.removeprefix("module."): v for k, v in state.items()})
            return model.to(self.device).eval()

        def _prepare_audio(self, audio_file):
            return audio_file  # Service has already produced mono 16 kHz WAV.

        def _merge_audio_video(self, audio_file, temp_video, outfile):
            subprocess.run([args.ffmpeg, "-nostdin", "-v", "error", "-i", audio_file,
                            "-i", temp_video, "-map", "1:v:0", "-map", "0:a:0",
                            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
                            "-shortest", outfile], check=True, timeout=120,
                           stdin=subprocess.DEVNULL)

    engine = LocalLipSync(model="wav2lip", checkpoint_path=args.checkpoint,
                          device=args.device, nosmooth=True, save_cache=False,
                          wav2lip_batch_size=args.batch_size)
    engine.sync(args.avatar, args.audio, args.output)


if __name__ == "__main__":
    main()
