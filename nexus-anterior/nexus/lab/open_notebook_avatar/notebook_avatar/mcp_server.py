"""Optional stdio MCP tools forwarding to the authenticated native REST API."""
import os
from urllib.parse import quote

import httpx
from mcp.server.fastmcp import FastMCP


server = FastMCP("Open Notebook Avatar")


def request(method, path, payload=None):
    # Fixed local origin, never a URL supplied by a tool/model.
    password = os.environ.get("OPEN_NOTEBOOK_PASSWORD", "")
    headers = {"Authorization": "Bearer " + password} if password else {}
    with httpx.Client(base_url="http://127.0.0.1:5055", headers=headers,
                      timeout=960, follow_redirects=False, trust_env=False) as client:
        response = client.request(method, path, json=payload)
        response.raise_for_status()
        if len(response.content) > 100_000:
            raise ValueError("Response too large")
        return response.json()


@server.tool()
def render_podcast_avatar(episode_id: str, avatar: str, device: str = "cpu", batch_size: int = 8) -> dict:
    """Render an existing Open Notebook episode with an operator-provided portrait."""
    return request("POST", "/api/podcasts/episodes/" + quote(episode_id, safe="") + "/avatar",
                   {"avatar": avatar, "device": device, "batch_size": batch_size})


@server.tool()
def get_podcast_avatar(job_id: str) -> dict:
    """Get validated video provenance without rendering or calling AI again."""
    if len(job_id) != 64 or any(c not in "0123456789abcdef" for c in job_id):
        raise ValueError("Invalid job id")
    return request("GET", "/api/podcasts/avatars/" + job_id)


if __name__ == "__main__":
    server.run(transport="stdio")
