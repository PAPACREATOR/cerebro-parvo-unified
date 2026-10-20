"""Native optional router: uses Open Notebook's existing episode and auth.

Mount inside api.main; do not serve this router as an unauthenticated app.
"""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field, StrictInt
from starlette.concurrency import run_in_threadpool
from typing import Literal

from .service import AvatarError, AvatarService, Settings


class RenderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    avatar: str = Field(min_length=1, max_length=120, pattern=r"^[\w .-]+\.(jpg|jpeg|png)$")
    device: Literal["cpu", "cuda"] = "cpu"
    batch_size: StrictInt = Field(default=8, ge=1, le=32)


def configured_service() -> AvatarService:
    from open_notebook.config import PODCASTS_FOLDER
    required = ["OPEN_NOTEBOOK_AVATAR_ROOT", "OPEN_NOTEBOOK_AVATAR_OUTPUT",
                "OPEN_NOTEBOOK_AVATAR_CHECKPOINT", "OPEN_NOTEBOOK_AVATAR_PYTHON"]
    if any(not os.environ.get(k) for k in required):
        raise AvatarError("AVATAR_NOT_CONFIGURED")
    return AvatarService(Settings(Path(PODCASTS_FOLDER), Path(os.environ[required[0]]),
                                 Path(os.environ[required[1]]), Path(os.environ[required[2]]),
                                 os.environ[required[3]], timeout=900))


async def native_episode(episode_id: str):
    from open_notebook.podcasts.models import PodcastEpisode
    from open_notebook.podcasts.audio_paths import resolve_contained_audio_path, podcasts_root
    from open_notebook.exceptions import InvalidInputError, NotFoundError
    episode = await PodcastEpisode.get(episode_id)
    if episode is None or not episode.audio_file:
        raise NotFoundError("Episode audio is unavailable")
    path = resolve_contained_audio_path(episode.audio_file)
    if path is None:
        raise InvalidInputError("Episode audio path is invalid")
    return path.relative_to(podcasts_root()).as_posix()


def translated(error: AvatarError):
    from open_notebook.exceptions import ConfigurationError, InvalidInputError, NotFoundError, ExternalServiceError
    if error.code in {"AVATAR_NOT_CONFIGURED", "CHECKPOINT_UNAVAILABLE", "TOOL_UNAVAILABLE"}:
        return ConfigurationError(error.code)
    if error.code in {"JOB_NOT_FOUND", "INPUT_UNAVAILABLE"}:
        return NotFoundError(error.code)
    if error.code in {"TOOL_TIMEOUT", "TOOL_FAILED", "JOB_BUSY"}:
        return ExternalServiceError(error.code)
    return InvalidInputError(error.code)


def create_router(service_factory=configured_service, episode_lookup=native_episode):
    router = APIRouter()

    @router.post("/podcasts/episodes/{episode_id}/avatar")
    async def render(episode_id: str, request: RenderRequest):
        try:
            audio_name = await episode_lookup(episode_id)
            service = service_factory()
            return await run_in_threadpool(service.render, episode_id, audio_name,
                                           request.avatar, request.device, request.batch_size)
        except AvatarError as error:
            raise translated(error) from None

    @router.get("/podcasts/avatars/{job_id}")
    def status(job_id: str):
        try:
            return service_factory().inspect(job_id)
        except AvatarError as error:
            raise translated(error) from None

    @router.get("/podcasts/avatars/{job_id}/video")
    def video(job_id: str):
        try:
            service = service_factory()
            service.inspect(job_id)
            return FileResponse(service.settings.output_root.resolve() / job_id / "video.mp4",
                                media_type="video/mp4", filename="avatar.mp4")
        except AvatarError as error:
            raise translated(error) from None

    return router


router = create_router()
