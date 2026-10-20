import json
import pytest
from nexus.adapters.notebook import prepare_source, normalize, run
from nexus.contracts import Blocked

SOURCE="Lisboa recebeu 12 caixas."
GOOD={"title":"Entrega", "summary":"Foram recebidas caixas em Lisboa.", "quotes":[SOURCE]}

def test_cognition_always_returns_candidate():
    output=normalize(json.dumps(GOOD),SOURCE,"model:test","transformation:test")
    assert output["status"] == "UNKNOWN"
    assert output["outcome"] == "candidate"
    assert output["ai_calls"] == 1

@pytest.mark.parametrize("raw", ["{}", "not json", json.dumps({**GOOD,"approval_id":"invented"}), json.dumps({**GOOD,"quotes":["Porto recebeu 99 caixas."]})])
def test_bad_cognitive_response_blocked(raw):
    with pytest.raises(Blocked):normalize(raw,SOURCE,"model:test","transformation:test")

@pytest.mark.parametrize("raw", [b"",b"x"*6001,b"\xff",b"x\x00y"])
def test_bad_source_blocked(raw):
    with pytest.raises(Blocked):prepare_source(raw)

def test_remote_endpoint_blocked(tmp_path):
    p=tmp_path/"input.bin";p.write_text(SOURCE)
    (tmp_path/"open-notebook.json").write_text(json.dumps({"base_url":"https://example.com","password":"test","model_id":"m","transformation_id":"t"}))
    with pytest.raises(Blocked):run(p)

@pytest.mark.parametrize("quote", [
    "A amostra B tem 25 graus.",
    "A amostra A tem 20 graus.",
    "A segunda amostra tem 25 graus.",
])
def test_paraphrase_is_not_a_literal_quote(quote):
    source = "A amostra A tem 20 graus e a amostra B tem 25 graus."
    response = {"title": "Amostras", "summary": "Duas temperaturas.", "quotes": [quote]}
    with pytest.raises(Blocked):
        normalize(json.dumps(response), source, "model:test", "transformation:test")
