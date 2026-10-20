"""Bounded cognitive call. No tool execution and no Canonical capability."""
import json
import sys
import urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from nexus.contracts import Blocked, strict_json, validate

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise Blocked("Redirecionamento da bancada proibido.")

def prepare_source(raw):
    try:
        text = raw.decode("utf-8")
    except UnicodeError as error:
        raise Blocked("A interpretação aceita texto UTF-8 nesta versão.") from error
    if not text.strip() or len(text) > 6000 or "\x00" in text:
        raise Blocked("Usa texto até 6000 caracteres nesta versão.")
    return text

def normalize(raw, source, model_id, transformation_id):
    value = strict_json(raw)
    validate("cognitive", value)
    if any(quote not in source for quote in value["quotes"]):
        raise Blocked("A resposta contém uma citação que não existe na fonte.")
    content = "# " + value["title"] + "\n\n" + value["summary"]
    content += "\n\n## Trechos da fonte\n" + "\n".join("> " + quote.replace("\n", "\n> ") for quote in value["quotes"])
    return {"status":"UNKNOWN", "outcome":"candidate", "title":value["title"],
            "markdown":content, "ai_calls":1,
            "evidence":[{"capability":"open-notebook/local-model", "status":"UNKNOWN",
                         "value":json.dumps({"model_id":model_id,"transformation_id":transformation_id,"quotes":value["quotes"]},ensure_ascii=False)}]}

def fetch_output(source, config):
    """Host-owned bounded HTTP action. The confined tool receives no credential."""
    if (not isinstance(config, dict) or set(config) != {"base_url","password","model_id","transformation_id"}
            or config["base_url"] != "http://127.0.0.1:5055"
            or any(not isinstance(v, str) or not v or len(v) > 4000 or "\x00" in v for v in config.values())):
        raise Blocked("Configuração da bancada não autorizada.")
    payload = {"model_id":config["model_id"],"transformation_id":config["transformation_id"],"input_text":source}
    request = urllib.request.Request(config["base_url"] + "/api/transformations/execute",
        data=json.dumps(payload).encode("utf-8"),headers={"Content-Type":"application/json","Authorization":"Bearer " + config["password"]})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    try:
        with opener.open(request,timeout=110) as response:
            raw = response.read(200001)
        if len(raw) > 200000:
            raise Blocked("Resposta demasiado grande.")
        envelope = strict_json(raw)
        output = envelope["output"]
        if not isinstance(output, str):
            raise Blocked("Resposta cognitiva sem texto estruturado.")
        return {"output": output, "model_id": config["model_id"], "transformation_id": config["transformation_id"]}
    except Blocked:
        raise
    except Exception as error:
        raise Blocked("A bancada não devolveu uma resposta utilizável.") from None


def run(input_path):
    path = Path(input_path)
    source = prepare_source(path.read_bytes())
    response = path.parent / "open-notebook-response.json"
    if sys.platform == "win32":
        from nexus.windows_sandbox import require_native_boundary
        require_native_boundary()
        # No network-capability widening and no secret/configuration fallback.
        if not response.is_file():
            raise Blocked("Falta a resposta delimitada da bancada.")
        value = strict_json(response.read_bytes())
    else:
        config = strict_json((path.parent / "open-notebook.json").read_bytes())
        value = fetch_output(source, config)
    if not isinstance(value, dict) or set(value) != {"output", "model_id", "transformation_id"}:
        raise Blocked("Resposta delimitada inválida.")
    return normalize(value["output"], source, value["model_id"], value["transformation_id"])

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        print(json.dumps(run(sys.argv[1]),ensure_ascii=False))
    except Exception:
        print("Bancada cognitiva indisponível ou resposta rejeitada.",file=sys.stderr)
        raise SystemExit(1)
