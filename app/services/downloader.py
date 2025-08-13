import os
import tempfile
from pathlib import Path

import aiofiles
import httpx

from app.config.base import settings
from app.models.audio import DownloadMetadata


class DownloaderService:
    async def download(self, url: str) -> DownloadMetadata:
        timeout = httpx.Timeout(settings.DOWNLOAD_TIMEOUT, connect=10.0)

        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        ) as client:

            try:
                response = await client.get(url)
                response.raise_for_status()
            except httpx.ConnectError:
                raise ConnectionError(f"Cannot connect to {url}")
            except httpx.HTTPStatusError as e:
                raise FileNotFoundError(f"HTTP {e.response.status_code}: {url}")

            content_type = response.headers.get("content-type", "")
            file_ext = self._get_extension(url, content_type)

            if response.content is None or len(response.content) == 0:
                raise ValueError("Downloaded file is empty")

            if len(response.content) > settings.MAX_FILE_SIZE:
                raise ValueError(f"File too large: {len(response.content)} bytes")

            temp_file = tempfile.NamedTemporaryFile(
                suffix=file_ext, dir=settings.TEMP_DIR, delete=False
            )
            temp_path = temp_file.name
            temp_file.close()

            async with aiofiles.open(temp_path, "wb") as f:
                await f.write(response.content)

            file_size = os.path.getsize(temp_path)

            return DownloadMetadata(
                url=url, content_type=content_type, file_size=file_size, temp_path=temp_path
            )

    def _get_extension(self, url: str, content_type: str) -> str:
        url_ext = Path(url).suffix.lower()
        valid_exts = [".mp3", ".wav", ".ogg", ".m4a", ".flac"]

        if url_ext in valid_exts:
            return url_ext

        content_map = {
            "audio/mpeg": ".mp3",
            "audio/wav": ".wav",
            "audio/ogg": ".ogg",
            "audio/mp4": ".m4a",
            "audio/flac": ".flac",
        }

        for ct, ext in content_map.items():
            if content_type.startswith(ct):
                return ext

        return ".mp3"

    @staticmethod
    def cleanup(file_path: str):
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except Exception:
            pass
