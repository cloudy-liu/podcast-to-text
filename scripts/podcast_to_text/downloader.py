from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

import requests
from tqdm import tqdm


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


def fetch_text(url: str, timeout: int = 30) -> str:
    response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
    response.raise_for_status()
    return response.text


def download_file(url: str, output_path: Path, timeout: int = 30) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, headers=DEFAULT_HEADERS, stream=True, timeout=timeout) as response:
        response.raise_for_status()
        total = int(response.headers.get("content-length") or 0)
        with output_path.open("wb") as file_obj:
            with tqdm(total=total, unit="B", unit_scale=True, disable=total == 0) as progress:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if not chunk:
                        continue
                    file_obj.write(chunk)
                    progress.update(len(chunk))
    return output_path


def audio_extension(audio_url: str) -> str:
    suffix = Path(urlparse(audio_url).path).suffix.lower()
    return suffix if suffix else ".audio"
