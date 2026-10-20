"""Fixed adapter dispatch inside the native boundary owned by Host.

No model, agent, reasoning, persistence or approval authority lives here.
External MCP remains an optional protocol, not this internal dispatch path.
"""
import hashlib
import json
import os
import sys
from pathlib import Path

# Load the known package directly: LPAC can read Nexus without being granted
# directory listing/read access to the repository or the human's parent folder.
if __package__ in (None, ""):
    import importlib.util
    package_root = Path(__file__).absolute().parents[1]
    package_spec = importlib.util.spec_from_file_location(
        "nexus", package_root / "__init__.py",
        submodule_search_locations=[str(package_root)])
    package = importlib.util.module_from_spec(package_spec)
    sys.modules["nexus"] = package
    package_spec.loader.exec_module(package)

from nexus.contracts import Blocked, ROOT, strict_json, validate


PROCESS_TO_TOOL = {
    "verify": "verify_file",
    "interpret": "interpret_file",
    "proofread": "proofread_file",
    "convert_pdf": "convert_pdf_file",
    "video": "video_plan_file",
    "podcast": "podcast_plan_file",
    "visual_podcast": "visual_podcast_plan_file",
    "book": "book_file",
    "music": "music_plan_file",
    "web": "web_plan_file",
}

PROCESS_FILES = {
    "verify": (
        "adapters/runner.py",
        "adapters/verify_direct.py", "adapters/tools.py",
    ),
    "interpret": (
        "adapters/runner.py",
        "adapters/notebook.py",
    ),
    "proofread": (
        "adapters/runner.py",
        "adapters/languagetool.py",
    ),
    "convert_pdf": (
        "adapters/runner.py",
        "adapters/office.py",
        "adapters/writer_sandy.py",
        "adapters/vendor/sandy/libreoffice-demo.py",
        "adapters/vendor/sandy/libreoffice.toml",
        "adapters/vendor/sandy/LICENSE",
    ),
    "video": (
        "adapters/runner.py",
        "adapters/product_routes.py",
    ),
    "podcast": (
        "adapters/runner.py",
        "adapters/product_routes.py",
    ),
    "visual_podcast": (
        "adapters/runner.py",
        "adapters/product_routes.py",
    ),
    "book": (
        "adapters/runner.py",
        "adapters/office.py",
        "adapters/writer_sandy.py",
        "adapters/vendor/sandy/libreoffice-demo.py",
        "adapters/vendor/sandy/libreoffice.toml",
        "adapters/vendor/sandy/LICENSE",
    ),
    "music": (
        "adapters/runner.py",
        "adapters/product_routes.py",
    ),
    "web": (
        "adapters/runner.py",
        "adapters/product_routes.py",
    ),
}


def process_fingerprint(process):
    files = PROCESS_FILES.get(process)
    if files is None:
        raise Blocked("Processo indisponível.")
    h = hashlib.sha256()
    h.update(process.encode("utf-8"))
    h.update(b"\0")
    for relative in (*files, "windows_sandbox.py", "contracts.py", "schemas/result.json"):
        path = ROOT / relative
        h.update(relative.encode("utf-8"))
        h.update(b"\0")
        h.update(path.read_bytes())
        h.update(b"\0")
    return h.hexdigest()


def _trace(process, tool):
    return {
        "engine": "nexus/python-direct",
        "version": "1.0.0",
        "process": process,
        "summary": {
            "usage": {"total_tokens": 0},
            "agents_executed": [tool],
        },
        "events": [{"type": "adapter.completed", "step": tool}],
    }



def prepare_task(process, input_path, work, *, config_root=None):
    """Trusted Host preparation: selected input copies, RO tools, no Store access."""
    if process not in PROCESS_TO_TOOL:
        raise Blocked("Processo indisponível.")
    source, work = Path(input_path), Path(work)
    raw = source.read_bytes()
    if not raw or len(raw) > 2_097_152:
        raise Blocked("Input fora do limite.")
    (work / "input.bin").write_bytes(raw)
    roots = [ROOT, Path(sys.prefix), Path(sys.base_prefix)]
    # Private TemporaryDirectory ancestors need read access for Windows path
    # normalization. This grants only this freshly assigned task subtree.
    if work.parent.name != "runs" or not work.parent.parent.name.startswith(".nexus-task-"):
        raise Blocked("Área de tarefa não autorizada.")
    roots.append(work.parent.parent)
    config_root = Path(config_root) if config_root is not None else source.parent
    if process == "interpret":
        from nexus.adapters.notebook import fetch_output, prepare_source
        if not (config_root / "open-notebook.json").is_file():
            raise Blocked("A interpretação precisa da bancada local configurada.")
        config = strict_json((config_root / "open-notebook.json").read_bytes())
        response = fetch_output(prepare_source(raw), config)
        (work / "open-notebook-response.json").write_text(
            json.dumps(response, ensure_ascii=False), encoding="utf-8")
    elif process in ("video", "podcast", "visual_podcast"):
        from nexus.adapters.product_routes import fetch_plan, prepare_text
        if not (config_root / "open-notebook-product.json").is_file():
            raise Blocked("A rota precisa do OpenNotebook local configurado.")
        config = strict_json((config_root / "open-notebook-product.json").read_bytes())
        response = fetch_plan(prepare_text(raw), process, config)
        (work / "product-plan-response.json").write_text(
            json.dumps(response, ensure_ascii=False), encoding="utf-8")
    elif process in ("proofread", "convert_pdf", "book"):
        name = "languagetool.json" if process == "proofread" else "libreoffice.json"
        if not (config_root / name).is_file():
            raise Blocked("A ferramenta precisa de configuração local.")
        config = strict_json((config_root / name).read_bytes())
        keys = {"java", "jar"} if process == "proofread" else {"executable", "sandy"}
        if not isinstance(config, dict) or set(config) != keys:
            raise Blocked("Configuração da ferramenta inválida.")
        for value in config.values():
            if not isinstance(value, str) or not Path(value).is_absolute() or not Path(value).is_file():
                raise Blocked("Ferramenta local indisponível.")
        if process == "proofread":
            java, jar = Path(config["java"]), Path(config["jar"])
            if java.name.lower() != "java.exe" or jar.name != "languagetool-commandline.jar":
                raise Blocked("Ferramenta não autorizada.")
            roots += [java.parent.parent, jar.parent]
        else:
            exe = Path(config["executable"])
            sandy = Path(config["sandy"])
            if exe.name.lower() != "soffice.com" or sandy.name.lower() != "sandy.exe":
                raise Blocked("Ferramenta não autorizada.")
            roots.append(exe.parent.parent)
        (work / name).write_text(json.dumps(config), encoding="utf-8")
    return tuple(dict.fromkeys(roots))


def collect_artifact(envelope, work, destination):
    """Only after the job has ended; copy a fixed, bounded and hash-checked PDF."""
    validate("result", envelope["result"])
    artifact = envelope["result"].get("artifact")
    if artifact:
        from nexus.adapters.office import pdf_bytes
        path = Path(work) / "resultado.pdf"
        if path.is_junction() or path.resolve().parent != Path(work).resolve():
            raise Blocked("Artefacto redirecionado.")
        data = pdf_bytes(path)
        if artifact["name"] != "resultado.pdf" or hashlib.sha256(data).hexdigest() != artifact["sha256"]:
            raise Blocked("Artefacto não corresponde à resposta.")
        from nexus.store import atomic
        atomic(Path(destination) / "resultado.pdf", data)


def _input(value):
    if os.name == "nt":
        from nexus.windows_sandbox import require_native_boundary
        require_native_boundary()
    path = Path(value)
    if (not path.is_absolute() or path.name != "input.bin" or not path.is_file()
            or path.is_symlink() or path.is_junction() or path.parent.is_junction()
            or path.parent.parent.name != "runs"
            or path.resolve().parent != path.parent.resolve()
            or (os.name == "nt" and path.parent.resolve() != Path.cwd().resolve())):
        raise Blocked("Input fora da área atribuída.")
    return path.resolve()


def _dispatch(process, path):
    if process == "verify":
        from nexus.adapters.verify_direct import execute
        return execute(path)["result"]
    if process == "interpret":
        from nexus.adapters.notebook import run
        return run(path)
    if process == "proofread":
        from nexus.adapters.languagetool import run
        return run(path)
    if process in ("convert_pdf", "book"):
        from nexus.adapters.office import run
        return run(path)
    if process in ("video", "podcast", "visual_podcast"):
        from nexus.adapters.product_routes import run_open_notebook
        return run_open_notebook(path, process)
    if process == "music":
        from nexus.adapters.product_routes import run_music
        return run_music(path)
    if process == "web":
        from nexus.adapters.product_routes import run_web
        return run_web(path)
    raise Blocked("Processo indisponível.")


def _direct_result(process, input_path):
    if process not in PROCESS_TO_TOOL:
        raise Blocked("Processo indisponível.")
    try:
        value = _dispatch(process, _input(input_path))
        raw = json.dumps(value, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
        if len(raw) > 1_000_000:
            raise Blocked("Resposta excede o limite Nexus.")
        return validate("result", strict_json(raw))
    except Blocked:
        raise
    except Exception as error:
        raise Blocked("Adapter falhou de forma controlada.") from error


def execute(process, input_path):
    result = _direct_result(process, input_path)
    return {"result": result, "trace": _trace(process, PROCESS_TO_TOOL[process])}


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        process, input_path = sys.argv[1:3]
        print(json.dumps(execute(process, input_path), ensure_ascii=False))
    except Exception:
        sys.stderr.reconfigure(encoding="utf-8")
        import traceback
        traceback.print_exc(limit=8)
        print("Execução direta indisponível ou resposta rejeitada.", file=sys.stderr)
        raise SystemExit(1)
