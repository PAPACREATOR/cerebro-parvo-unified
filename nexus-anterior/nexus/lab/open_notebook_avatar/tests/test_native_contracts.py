"""Tests against upstream Open Notebook exception/auth code when available.

Set PYTHONPATH to a pristine Open Notebook v1.14.0 source checkout; this does
not need its DB/provider stack. Full native DB acceptance is run separately.
"""
import importlib.util
from pathlib import Path
import sys

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

native = pytest.importorskip("open_notebook.exceptions", reason="Native Open Notebook source required")
from api.auth import PasswordAuthMiddleware
from notebook_avatar.router import RenderRequest, create_router, translated
from notebook_avatar.service import AvatarError


@pytest.mark.parametrize("code,type", [
    ("AVATAR_NOT_CONFIGURED", native.ConfigurationError),
    ("CHECKPOINT_UNAVAILABLE", native.ConfigurationError),
    ("TOOL_UNAVAILABLE", native.ConfigurationError),
    ("INPUT_UNAVAILABLE", native.NotFoundError),
    ("JOB_NOT_FOUND", native.NotFoundError),
    ("TOOL_FAILED", native.ExternalServiceError),
    ("TOOL_TIMEOUT", native.ExternalServiceError),
    ("JOB_BUSY", native.ExternalServiceError),
    ("OUTPUT_TAMPERED", native.InvalidInputError),
    ("INVALID_OPTIONS", native.InvalidInputError),
    ("AVATAR_INVALID", native.InvalidInputError),
    ("INVALID_JOB", native.InvalidInputError),
])
def test_error_mapping(code, type):
    assert isinstance(translated(AvatarError(code)), type)


@pytest.mark.parametrize("header", [None, "", "Basic ARCHIVE_REDACTED_02", "Bearer wrong", "invalid",
                                     "Bearer", "bearer wrong", "Bearer ARCHIVE_REDACTED_02 "])
def test_upstream_auth_prevents_capability_execution(monkeypatch, header):
    monkeypatch.setenv("OPEN_NOTEBOOK_PASSWORD", "ARCHIVE_REDACTED_02")
    calls = []
    class Service:
        def render(self, *a):
            calls.append(a)
            return {"unexpected": True}
    async def lookup(episode):
        calls.append(episode)
        return "episode.wav"
    app = FastAPI()
    app.add_middleware(PasswordAuthMiddleware)
    app.include_router(create_router(lambda: Service(), lookup), prefix="/api")
    headers = {} if header is None else {"Authorization": header}
    response = TestClient(app).post("/api/podcasts/episodes/episode:one/avatar",
                                    json={"avatar": "face.png"}, headers=headers)
    assert response.status_code == 401
    assert calls == []


@pytest.mark.parametrize("payload", [{"avatar":"face.png","batch_size":1},
    {"avatar":"face.png","batch_size":32}, {"avatar":"ação.png","device":"cpu"},
    {"avatar":"漢字.png","device":"cuda"}, {"avatar":"portrait 1.jpg"}, {"avatar":"portrait.jpeg"}])
def test_request_valid_limits(payload):
    assert RenderRequest.model_validate(payload).avatar == payload["avatar"]


@pytest.mark.parametrize("key", ["", "../x", "x"*64, "f"*63, "f"*65, "F"*64, "0"*63+"\n", "a/"*32])
def test_bad_job_ids_do_not_touch_media(setup, key):
    with pytest.raises(AvatarError) as error:
        setup.inspect(key)
    assert error.value.code == "INVALID_JOB"
    assert list(setup.settings.output_root.iterdir()) == []


@pytest.mark.parametrize("version,anchor", [("1.14.0", "app=object()\n"), ("1.14.0", "# Nexus optional Open Notebook avatar extension\n")])
def test_installer_refuses_unknown_layout(tmp_path, version, anchor):
    path = Path(__file__).parents[1] / "install_router.py"
    spec = importlib.util.spec_from_file_location("installer", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    (tmp_path / "api").mkdir()
    (tmp_path / "api/main.py").write_text(anchor)
    (tmp_path / "pyproject.toml").write_text('[project]\nversion="'+version+'"\n')
    with pytest.raises(ValueError):module.install(tmp_path)
    assert (tmp_path / "api/main.py").read_text() == anchor
    assert not (tmp_path / "api/main.py.pre-avatar").exists()
