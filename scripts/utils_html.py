# -*- coding: utf-8 -*-
import os, hashlib, pathlib
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import requests
import html2text
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]

def html_to_markdown_with_local_images(html: str, ts: int, article_id: str, img_root: pathlib.Path):
    """Convert WeChat HTML into Markdown while localizing images.

    Steps
    - Parse <img> tags, download data-src/src images to a local path.
    - Rewrite <img src> to repository-relative path so it renders on GitHub.
    - Convert the updated HTML to Markdown (keep links and images).

    参数/Params
    - html: 原始 HTML 字符串 / raw HTML string
    - ts: 文章时间戳（用于分年存储图片） / unix timestamp of the article
    - article_id: 文章或素材标识 / article or material identifier
    - img_root: 图片根目录，如 assets/wechat/ / image root dir
    """
    soup = BeautifulSoup(html or "", "html.parser")
    img_dir = img_root / datetime.fromtimestamp(ts).strftime("%Y") / article_id
    img_dir.mkdir(parents=True, exist_ok=True)

    for img in soup.find_all("img"):
        src = img.get("data-src") or img.get("src")
        if not src:
            continue
        try:
            h = hashlib.md5(src.encode("utf-8")).hexdigest()[:12]
            ext = pathlib.Path(urlparse(src).path).suffix or ".jpg"
            local_path = img_dir / f"{h}{ext}"
            if not local_path.exists():
                r = requests.get(src, timeout=30)
                r.raise_for_status()
                local_path.write_bytes(r.content)
            rel = os.path.relpath(local_path, ROOT).replace("\\", "/")
            img["src"] = "/" + rel
            if img.has_attr("data-src"):
                img["data-src"] = img["src"]
        except Exception:
            # 忽略单张失败，继续
            continue

    # 转 Markdown
    h2t = html2text.HTML2Text()
    h2t.ignore_links = False
    h2t.ignore_images = False
    md = h2t.handle(str(soup))
    return md
